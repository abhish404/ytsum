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
from transcript import build_markdown
from filler import remove_fillers
from summarize import summarize


def main():
    if len(sys.argv) < 2:
        url = input("Paste YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    transcript_path = "transcript.md"

    # Step 1: Fetch transcript
    print("═" * 50)
    print("STEP 1: Fetching transcript...")
    print("═" * 50)
    markdown = build_markdown(url)
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"✅ Transcript saved ({len(markdown.split())} words)\n")

    # Step 2: Remove fillers
    print("═" * 50)
    print("STEP 2: Removing filler words...")
    print("═" * 50)
    cleaned = remove_fillers(markdown)
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    removed = len(markdown.split()) - len(cleaned.split())
    print(f"✅ Cleaned transcript ({removed} filler words removed)\n")

    # Step 3: Summarize
    print("═" * 50)
    print("STEP 3: Summarizing...")
    print("═" * 50)
    summarize(transcript_path)

    print("\n🎉 Done! Check summary.md for results.")


if __name__ == "__main__":
    main()
