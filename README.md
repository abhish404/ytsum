# Flick - YouTube Summarizer

Summarize any YouTube video from the terminal or directly from your browser via a Chrome extension. Powered by Groq — a typical 10-minute video takes under 20 seconds.

---

## Prerequisites

- **Python 3.10+** must be installed
- A free **Groq API key** — get one at [console.groq.com](https://console.groq.com)
- *(Optional)* A Notion **Public Integration** to export summaries — set one up at [notion.so/my-integrations](https://www.notion.so/my-integrations)

---

## Installation

```bash
git clone https://github.com/abhish404/ytsum
cd ytsum
pip install groq yt-dlp youtube-transcript-api notion-client httpx fastapi uvicorn sse-starlette
```

Add your Groq key:

```bash
mkdir Keys
echo "your_groq_api_key" > Keys/groq.txt
```

---

## Running — Two Ways

### 1. CLI (terminal)

```bash
python main.py https://www.youtube.com/watch?v=...
# or just run and paste when prompted
python main.py
```

Output lands in `summary.md`. At the end you'll be asked if you want to push it to Notion.

### 2. Chrome Extension

**Start the backend first:**

```bash
python server.py
# or: uvicorn server:app --host 0.0.0.0 --port 8000
```

**Load the extension in Chrome:**

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder

Once loaded, navigate to any YouTube video. A sidebar appears below the video with a **Summarize** button. The extension popup (toolbar icon) works the same way and lets you change the backend URL under Settings.

Summaries are saved automatically to a `summaries/` folder as timestamped `.md` files.

---

## How It Works

### CLI pipeline

```
YouTube URL
    │
    ├─ yt-dlp                  → video metadata + chapter timestamps
    └─ youtube-transcript-api  → raw transcript
            (both fetched in parallel)
    │
    ▼
filler.py — strips um, uh, like, you know, basically, literally,
            kinda, sort of, i mean, okay, etc. + removes repeated words
    │
    ▼
summarize.py — if the video has chapters, each chapter is summarized
               in parallel via Groq, then a TL;DR is generated from
               all chapter summaries combined.
               Videos without chapters are summarized as one block.
               Chapters over 5000 words are split into chunks,
               summarized individually, then merged back.
    │
    ▼
summary.md  +  (optional) Notion page
```

**Models used:**
- Chapter summaries → `moonshotai/kimi-k2-instruct`
- TL;DR → `llama-3.1-8b-instant`

Both are on Groq's free tier. Every run appends an entry to `timings.json` — video title, word count, fillers removed, and per-step timing.

### Extension pipeline

The extension runs a two-phase pipeline so you see progress as it happens rather than waiting for everything at once.

**Phase 1 — Prepare** (runs automatically when you open the popup or sidebar on a YouTube video):
- The background service worker extracts your YouTube cookies from the browser
- Sends them along with the video URL to `POST /prepare` on the local server
- The server fetches the transcript via yt-dlp + youtube-transcript-api and strips filler words
- Returns the cleaned transcript as JSON

**Phase 2 — Summarize** (starts when you click the button):
- Sends the cleaned transcript to `POST /summarize`
- The server streams progress back over SSE — you see each step appear in real time
- The final summary renders as formatted Markdown in the sidebar/popup

The background service worker persists state across popup open/close via `chrome.storage.local`, so closing and reopening the popup doesn't lose your summary or restart the pipeline. If the service worker restarts mid-operation, it detects this on next load and surfaces an error rather than silently hanging.

**Server endpoints:**

| Endpoint | What it does |
|---|---|
| `POST /prepare` | Fetches transcript + removes fillers. Returns JSON. |
| `POST /summarize` | Summarizes a cleaned transcript. Streams progress + result via SSE. |
| `POST /summarize-full` | Combined single-call pipeline. Streams the full pipeline via SSE. |
| `GET /health` | Health check. Returns `{"status": "ok"}`. |

The extension passes your browser's YouTube cookies with each request so yt-dlp can access age-restricted or members-only videos. The server writes them to a temporary Netscape-format cookie file and deletes it after the request completes.

---

## Notion Setup (optional)

Notion uses OAuth — you authorize once and the token is saved for all future runs.

1. Create a **Public Integration** at [notion.so/my-integrations](https://www.notion.so/my-integrations) with redirect URI set to `http://localhost:3456/callback`
2. Save your credentials:

```bash
echo '{"client_id": "...", "client_secret": "..."}' > Keys/notion_oauth.json
```

On first use a browser window opens for authorization. After you approve, `Keys/notion_token.json` is saved and future runs skip the browser step. You'll be prompted to pick which Notion page to nest the summary under.

---

## Prompts

The AI prompts live in `Prompts/`:

- `Prompts/ch_prompt.txt` — per-chapter summarization instructions
- `Prompts/tldr_prompt.txt` — overall TL;DR instructions

Edit these to change the output format, level of detail, or tone.

---

## Keys folder

```
Keys/
├── groq.txt              ← Groq API key (plain text)
├── notion_oauth.json     ← Notion client_id + client_secret
└── notion_token.json     ← auto-created after first OAuth login
```

The `Keys/` directory is in `.gitignore`. Don't commit it.
