#!/usr/bin/env python3
"""
YouTube Transcript Fetcher with Chapters
Outputs a clean markdown file with ### chapter headings.

Usage:
    python get_transcript.py <youtube_url>
    python get_transcript.py  (will prompt for URL)

Requirements:
    pip install youtube-transcript-api yt-dlp
"""

import sys
import re
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_chapters(url: str) -> list[dict]:
    """Fetch chapter list from video metadata via yt-dlp."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("chapters") or []


def clean_text(text: str) -> str:
    return " ".join(text.replace(">>", "").split())


def build_markdown(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        print("❌ Could not extract video ID from URL.")
        sys.exit(1)

    print(f"📹 Video ID: {video_id}")
    print("⏳ Fetching chapters...")
    chapters = get_chapters(url)

    print("⏳ Fetching transcript...")
    ytt = YouTubeTranscriptApi()
    transcript = list(ytt.fetch(video_id))

    lines = []

    if chapters:
        print(f"✅ Found {len(chapters)} chapters — merging with transcript...\n")

        for i, chapter in enumerate(chapters):
            start = chapter["start_time"]
            end = chapters[i + 1]["start_time"] if i + 1 < len(chapters) else float("inf")
            title = chapter["title"]

            lines.append(f"### {i + 1}: {title}\n")

            # Collect transcript entries that fall within this chapter's time range
            segment_texts = [
                entry.text
                for entry in transcript
                if start <= entry.start < end
            ]
            chapter_text = clean_text(" ".join(segment_texts))
            lines.append(chapter_text + "\n")

    else:
        print("⚠️  No chapters found — outputting full transcript.\n")
        full_text = clean_text(" ".join(entry.text for entry in transcript))
        lines.append(full_text)

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = input("Paste YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    markdown = build_markdown(url)

    # Save to file
    output_file = "transcript.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    word_count = len(markdown.split())
    print(f"✅ Saved to transcript.md ({word_count} words)")
    print("\n--- Preview (first 500 chars) ---")
    print(markdown[:500])