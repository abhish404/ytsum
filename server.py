#!/usr/bin/env python3
"""
FastAPI backend for the YouTube Summarizer Chrome Extension.

Endpoints:
    POST /summarize  — accepts {url, cookies}, streams progress via SSE, returns summary

Usage:
    python server.py
    # or: uvicorn server:app --host 0.0.0.0 --port 8000
"""

import os
import json
import asyncio
import tempfile
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from transcript import build_markdown
from filler import remove_fillers
from summarize import summarize_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 YouTube Summarizer backend is running")
    yield

app = FastAPI(title="YouTube Summarizer API", lifespan=lifespan)

# Allow Chrome extension origins + localhost for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Chrome extension origins are opaque; allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def cookies_to_netscape_file(cookies: list[dict]) -> str:
    """Convert Chrome extension cookies to a Netscape-format cookie file.
    
    Returns the path to a temporary cookie file.
    """
    lines = ["# Netscape HTTP Cookie File", "# https://curl.se/docs/http-cookies.html", ""]
    for c in cookies:
        domain = c.get("domain", "")
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        expiry = str(int(c.get("expirationDate", 0)))
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")

    # Write to temp file (not auto-deleted so yt-dlp can read it)
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="yt_cookies_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


@app.post("/summarize")
async def summarize_video(request: Request):
    """Run the full summarization pipeline with SSE progress streaming."""
    body = await request.json()
    url = body.get("url", "").strip()
    cookies = body.get("cookies", [])

    if not url:
        return JSONResponse({"error": "Missing 'url' field"}, status_code=400)

    async def event_generator():
        cookiefile = None
        try:
            # Step 1: Write cookies to temp file
            yield {"event": "progress", "data": json.dumps({"step": "cookies", "message": "🍪 Processing cookies..."})}
            if cookies:
                cookiefile = cookies_to_netscape_file(cookies)
            await asyncio.sleep(0)

            # Step 2: Fetch transcript
            yield {"event": "progress", "data": json.dumps({"step": "transcript", "message": "📥 Fetching transcript..."})}
            loop = asyncio.get_event_loop()
            markdown, metadata = await loop.run_in_executor(
                None, lambda: build_markdown(url, cookiefile=cookiefile)
            )

            raw_words = len(markdown.split())
            yield {"event": "progress", "data": json.dumps({
                "step": "transcript_done",
                "message": f"📥 Transcript fetched ({raw_words} words)",
                "metadata": metadata,
            })}

            # Step 3: Remove fillers
            yield {"event": "progress", "data": json.dumps({"step": "filler", "message": "🧹 Removing filler words..."})}
            cleaned = await loop.run_in_executor(None, lambda: remove_fillers(markdown))
            removed = raw_words - len(cleaned.split())
            yield {"event": "progress", "data": json.dumps({
                "step": "filler_done",
                "message": f"🧹 Removed {removed} filler words",
            })}

            # Step 4: Summarize — use a Queue for real-time progress streaming
            yield {"event": "progress", "data": json.dumps({"step": "summarize", "message": "🤖 Summarizing with AI..."})}

            progress_queue = asyncio.Queue()

            def on_progress(msg: str):
                """Called from the sync thread — puts messages on the async queue."""
                loop.call_soon_threadsafe(progress_queue.put_nowait, ("progress", msg))

            def run_summarize():
                result = summarize_text(cleaned, progress_callback=on_progress)
                loop.call_soon_threadsafe(progress_queue.put_nowait, ("done", result))

            # Start summarization in a thread
            asyncio.ensure_future(loop.run_in_executor(None, run_summarize))

            # Stream progress events as they arrive from the thread
            while True:
                kind, value = await progress_queue.get()
                if kind == "progress":
                    yield {"event": "progress", "data": json.dumps({"step": "summarize_progress", "message": value})}
                elif kind == "done":
                    summary_md = value
                    break

            # Final result
            yield {"event": "result", "data": json.dumps({
                "summary": summary_md,
                "metadata": metadata,
                "stats": {
                    "transcript_words": raw_words,
                    "fillers_removed": removed,
                    "summary_words": len(summary_md.split()),
                },
            })}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        finally:
            # Clean up temp cookie file
            if cookiefile and os.path.exists(cookiefile):
                try:
                    os.unlink(cookiefile)
                except OSError:
                    pass

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
