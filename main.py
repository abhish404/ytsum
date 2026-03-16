#!/usr/bin/env python3
"""
main.py — End-to-end YouTube video summarizer.

Usage:
    python main.py <youtube_url>
    python main.py              (will prompt for URL)

Pipeline:
    1. Fetch transcript + chapters  → transcript.md
    2. Remove filler words          → transcript.md (cleaned in place)
    3. Summarize with Groq          → summary.md
"""

import sys
import os
import time
import json
from datetime import datetime
from transcript import build_markdown
from filler import remove_fillers
from summarize import summarize
from notion_export import export_summary

TIMINGS_FILE = "timings.json"


def load_timings() -> list:
    """Load existing timings log or return empty list."""
    if os.path.exists(TIMINGS_FILE):
        with open(TIMINGS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Handle old format (single dict) → wrap in list
                if isinstance(data, dict):
                    return [data]
                return data
            except json.JSONDecodeError:
                return []
    return []


def main():
    if len(sys.argv) < 2:
        url = input("Paste YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    transcript_path = "transcript.md"
    timings = {}
    pipeline_start = time.time()

    # Step 1: Fetch transcript
    print("═" * 50)
    print("STEP 1: Fetching transcript...")
    print("═" * 50)
    t0 = time.time()
    markdown, metadata = build_markdown(url)
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    timings["transcript_fetch"] = round(time.time() - t0, 2)
    print(f"✅ Transcript saved ({len(markdown.split())} words) [{timings['transcript_fetch']}s]\n")

    # Step 2: Remove fillers
    print("═" * 50)
    print("STEP 2: Removing filler words...")
    print("═" * 50)
    t0 = time.time()
    cleaned = remove_fillers(markdown)
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    removed = len(markdown.split()) - len(cleaned.split())
    timings["filler_removal"] = round(time.time() - t0, 2)
    print(f"✅ Cleaned transcript ({removed} filler words removed) [{timings['filler_removal']}s]\n")

    # Step 3: Summarize
    print("═" * 50)
    print("STEP 3: Summarizing...")
    print("═" * 50)
    t0 = time.time()
    summarize(transcript_path)
    timings["summarization"] = round(time.time() - t0, 2)

    # Step 4: Optional Notion export
    notion_url = None
    push = input("\n📤 Push to Notion? (y/n): ").strip().lower()
    if push in ("y", "yes"):
        print("═" * 50)
        print("STEP 4: Exporting to Notion...")
        print("═" * 50)
        t0 = time.time()
        video_title = metadata.get("title", "YouTube Summary")
        notion_url = export_summary(video_title)
        timings["notion_export"] = round(time.time() - t0, 2)

    timings["total"] = round(time.time() - pipeline_start, 2)

    # Build the full log entry
    duration = metadata.get("duration_seconds", 0)
    m, s = divmod(int(duration), 60)
    h, m = divmod(m, 60)
    duration_fmt = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "video": {
            "title": metadata.get("title", "Unknown"),
            "video_id": metadata.get("video_id", ""),
            "url": metadata.get("url", ""),
            "uploader": metadata.get("uploader", "Unknown"),
            "duration": duration_fmt,
            "duration_seconds": duration,
            "chapters": metadata.get("chapter_count", 0),
            "transcript_language": metadata.get("transcript_language", ""),
            "word_count": len(markdown.split()),
            "fillers_removed": removed,
        },
        "timings": timings,
    }
    if notion_url:
        entry["notion_url"] = notion_url

    # Append to existing log
    all_entries = load_timings()
    all_entries.append(entry)
    with open(TIMINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Done! Check summary.md for results.")
    print(f"⏱️  Timing log → {TIMINGS_FILE} ({len(all_entries)} entries)")
    print(json.dumps(entry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
