#!/usr/bin/env python3
"""
Simple YouTube Transcript Fetcher
Usage: python get_transcript.py <youtube_url>
"""

import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})",   # standard & short URLs
        r"youtu\.be\/([0-9A-Za-z_-]{11})",  # youtu.be links
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(url: str) -> None:
    video_id = extract_video_id(url)
    if not video_id:
        print("❌ Could not extract video ID from URL.")
        sys.exit(1)

    print(f"📹 Video ID: {video_id}")
    print("⏳ Fetching transcript...\n")

    # Instantiate the class (required in v0.6.0+)
    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id)

    full_text = " ".join(entry.text for entry in transcript)
    full_text = " ".join(full_text.replace(">>", "").split())

    print("=" * 60)
    print("TRANSCRIPT")
    print("=" * 60)
    print(full_text)
    print("=" * 60)
    print(f"\n✅ Done! ({len(transcript)} segments, {len(full_text.split())} words)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = input("Paste YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    get_transcript(url)