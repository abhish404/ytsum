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
import time
import json
from transcript import build_markdown
from filler import remove_fillers
from summarize import summarize


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
    markdown = build_markdown(url)
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

    timings["total"] = round(time.time() - pipeline_start, 2)

    # Save timing logs as JSON
    with open("timings.json", "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2)

    print(f"\n🎉 Done! Check summary.md for results.")
    print(f"⏱️  Timing log → timings.json")
    print(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
