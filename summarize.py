#!/usr/bin/env python3
"""
YouTube Transcript Summarizer using Groq
Reads transcript.md and outputs summary.md — summarizes chapter by chapter
to stay within free tier token limits.

Usage:
    python summarize.py                      # reads transcript.md by default
    python summarize.py my_transcript.md     # or pass a custom file

Requirements:
    pip install groq
    Get your free key at: https://console.groq.com — save it in groq.txt
"""

import sys
import re
import time
from groq import Groq


def load_prompt(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ {filename} not found — create it and add your prompt inside.")
        sys.exit(1)


def load_api_key() -> str:
    try:
        with open("groq.txt", "r") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("❌ groq.txt not found — create it and paste your API key inside.")
        print("   Get your free key at: https://console.groq.com")
        sys.exit(1)

    if not api_key:
        print("❌ groq.txt is empty — paste your API key inside it.")
        sys.exit(1)

    return api_key


def parse_chapters(transcript: str) -> list[dict]:
    """Split transcript markdown into chapters."""
    # Split on ### headings
    parts = re.split(r"(### .+)", transcript)
    chapters = []
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            chapters.append({"heading": heading, "body": body})
    return chapters


def call_groq(client: Groq, prompt: str, model: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < retries - 1:
                wait = 60  # wait 60s and retry
                print(f"   ⚠️  Rate limit hit — waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise
    return ""


def summarize(transcript_path: str) -> None:
    if not __import__("os").path.exists(transcript_path):
        print(f"❌ File not found: {transcript_path}")
        sys.exit(1)

    api_key = load_api_key()

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    chapters = parse_chapters(transcript)
    if not chapters:
        print("⚠️  No chapters found in transcript — make sure it uses ### headings.")
        sys.exit(1)

    print(f"📄 Found {len(chapters)} chapters to summarize")
    client = Groq(api_key=api_key)

    chapter_summaries = []
    for i, chapter in enumerate(chapters):
        print(f"⏳ Summarizing chapter {i + 1}/{len(chapters)}: {chapter['heading']}")
        chapter_prompt = load_prompt("ch_prompt.txt")
        summary = call_groq(client, chapter_prompt + "\n\n" + chapter["heading"] + "\n\n" + chapter["body"], model="llama-3.3-70b-versatile")
        chapter_summaries.append((chapter["heading"], summary))
        time.sleep(2)  # small delay between calls to avoid rate limits

    # Now generate overall TL;DR from chapter summaries
    print("⏳ Generating overall TL;DR...")
    combined = "\n\n".join([f"{h}\n{s}" for h, s in chapter_summaries])
    tldr_prompt = load_prompt("tldr_prompt.txt")
    tldr = call_groq(client, tldr_prompt + "\n\n" + combined, model="llama-3.1-8b-instant")

    # Build final markdown
    lines = []
    lines.append("## TL;DR")
    lines.append(tldr)
    lines.append("")
    lines.append("## Chapter Summaries")
    lines.append("")
    for heading, summary in chapter_summaries:
        lines.append(heading)
        lines.append(summary)
        lines.append("")

    output = "\n".join(lines)

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ Summary saved to summary.md")
    print("\n--- Preview ---")
    print(output[:600])


if __name__ == "__main__":
    transcript_path = sys.argv[1] if len(sys.argv) > 1 else "transcript.md"
    summarize(transcript_path)