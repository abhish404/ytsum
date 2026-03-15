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


def get_video_info(url: str) -> dict:
    """Fetch video metadata via yt-dlp."""
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def format_timestamp(seconds: float) -> str:
    """Convert seconds to M:SS or H:MM:SS format."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def clean_text(text: str) -> str:
    return " ".join(text.replace(">>", "").split())


def build_markdown(url: str) -> tuple[str, dict]:
    video_id = extract_video_id(url)
    if not video_id:
        print("❌ Could not extract video ID from URL.")
        sys.exit(1)

    print(f"📹 Video ID: {video_id}")
    print("⏳ Fetching video info...")
    info = get_video_info(url)
    chapters = info.get("chapters") or []

    metadata = {
        "video_id": video_id,
        "title": info.get("title", "Unknown"),
        "url": url,
        "duration_seconds": info.get("duration", 0),
        "uploader": info.get("uploader", "Unknown"),
        "chapter_count": len(chapters),
    }

    print("⏳ Fetching transcript...")
    ytt = YouTubeTranscriptApi()

    # Auto-detect available transcript language (supports any language)
    transcript_list = ytt.list(video_id)
    available = list(transcript_list)
    if not available:
        print("❌ No transcripts available for this video.")
        sys.exit(1)

    chosen = available[0]
    print(f"🌐 Found transcript: {chosen.language} ({chosen.language_code})")
    metadata["transcript_language"] = f"{chosen.language} ({chosen.language_code})"
    transcript = list(chosen.fetch())

    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    lines = []

    def ts_link(seconds: float) -> str:
        """Return a clickable markdown timestamp link."""
        label = format_timestamp(seconds)
        return f"[{label}]({yt_url}&t={int(seconds)}s)"

    def grouped_lines(entries: list, interval: float = 8.0) -> list[str]:
        """Group transcript entries into ~interval-second chunks."""
        if not entries:
            return []
        result = []
        group_start = entries[0].start
        group_texts = []
        for entry in entries:
            if entry.start - group_start >= interval and group_texts:
                result.append(f"{ts_link(group_start)} {clean_text(' '.join(group_texts))}")
                group_start = entry.start
                group_texts = []
            group_texts.append(entry.text)
        if group_texts:
            result.append(f"{ts_link(group_start)} {clean_text(' '.join(group_texts))}")
        return result

    if chapters:
        print(f"✅ Found {len(chapters)} chapters — merging with transcript...\n")

        for i, chapter in enumerate(chapters):
            start = chapter["start_time"]
            end = chapters[i + 1]["start_time"] if i + 1 < len(chapters) else float("inf")
            title = chapter["title"]

            lines.append(f"### {i + 1}: {title} {ts_link(start)}\n")

            chapter_entries = [e for e in transcript if start <= e.start < end]
            lines.extend(grouped_lines(chapter_entries))
            lines.append("")

    else:
        print("⚠️  No chapters found — outputting full transcript.\n")
        lines.extend(grouped_lines(transcript))

    return "\n".join(lines), metadata


if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = input("Paste YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    markdown, metadata = build_markdown(url)

    # Save to file
    output_file = "transcript.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    word_count = len(markdown.split())
    print(f"✅ Saved to transcript.md ({word_count} words)")
    print("\n--- Preview (first 500 chars) ---")
    print(markdown[:500])