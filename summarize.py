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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    parts = re.split(r"(### .+)", transcript)
    chapters = []
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            chapters.append({"heading": heading, "body": body})
    return chapters


def chunk_text(text: str, max_words: int = 5000) -> list[str]:
    """
    Split text into chunks where each chunk is at most max_words words.
    Splits on sentence boundaries where possible to avoid cutting mid-sentence.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    current_words = []

    for word in words:
        current_words.append(word)
        # At the word limit, try to break at sentence end
        if len(current_words) >= max_words:
            chunk = " ".join(current_words)
            # Find last sentence-ending punctuation to break cleanly
            last_break = max(chunk.rfind(". "), chunk.rfind("? "), chunk.rfind("! "))
            if last_break != -1:
                chunks.append(chunk[:last_break + 1].strip())
                remainder = chunk[last_break + 1:].strip()
                current_words = remainder.split() if remainder else []
            else:
                chunks.append(chunk)
                current_words = []

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


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
                wait = 60
                print(f"   ⚠️  Rate limit hit — waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise
    return ""


def summarize_chapter(client: Groq, chapter_prompt: str, heading: str, body: str) -> str:
    """
    Summarize a single chapter. If the body exceeds 5000 words, split it into
    chunks, summarize each chunk separately, then merge into a final summary.
    """
    words = body.split()

    if len(words) <= 5000:
        # Normal path — chapter fits in one call
        return call_groq(
            client,
            chapter_prompt + "\n\n" + heading + "\n\n" + body,
            model="moonshotai/kimi-k2-instruct"
        )

    # Chapter is too large — chunk it
    chunks = chunk_text(body, max_words=5000)
    print(f"   📦 Chapter too large ({len(words)} words), splitting into {len(chunks)} chunks...")

    chunk_summaries = []
    for j, chunk in enumerate(chunks):
        print(f"      ↳ Chunk {j + 1}/{len(chunks)}...")
        chunk_summary = call_groq(
            client,
            chapter_prompt + "\n\n" + heading + f" (part {j + 1}/{len(chunks)})" + "\n\n" + chunk,
            model="moonshotai/kimi-k2-instruct"
        )
        chunk_summaries.append(chunk_summary)
        time.sleep(2)

    # Merge chunk summaries into one cohesive chapter summary
    merge_prompt = (
        "The following are partial summaries of different sections of the same chapter. "
        "Merge them into a single cohesive set of notes without repeating yourself. "
        "Keep the note-style format.\n\n"
        + "\n\n".join(chunk_summaries)
    )
    return call_groq(client, merge_prompt, model="moonshotai/kimi-k2-instruct")


def summarize(transcript_path: str) -> None:
    if not __import__("os").path.exists(transcript_path):
        print(f"❌ File not found: {transcript_path}")
        sys.exit(1)

    api_key = load_api_key()

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    client = Groq(api_key=api_key)
    chapter_prompt = load_prompt("ch_prompt.txt")
    tldr_prompt = load_prompt("tldr_prompt.txt")

    chapters = parse_chapters(transcript)

    if chapters:
        # --- Path A: video has chapters ---
        total = len(chapters)
        print(f"📄 Found {total} chapters to summarize (parallel)")

        # Summarize all chapters in parallel
        chapter_summaries = [None] * total

        def _summarize(idx, chapter):
            print(f"⏳ [{idx + 1}/{total}] {chapter['heading']}")
            summary = summarize_chapter(client, chapter_prompt, chapter["heading"], chapter["body"])
            return idx, chapter["heading"], summary

        with ThreadPoolExecutor(max_workers=total) as pool:
            futures = [pool.submit(_summarize, i, ch) for i, ch in enumerate(chapters)]
            for future in as_completed(futures):
                idx, heading, summary = future.result()
                chapter_summaries[idx] = (heading, summary)
                print(f"✅ [{idx + 1}/{total}] done")

        # TL;DR from chapter summaries
        print("⏳ Generating overall TL;DR...")
        combined = "\n\n".join([f"{h}\n{s}" for h, s in chapter_summaries])
        tldr = call_groq(client, tldr_prompt + "\n\n" + combined, model="llama-3.1-8b-instant")

        # Build final markdown
        lines = ["## TL;DR", tldr, "", "## Chapter Summaries", ""]
        for heading, summary in chapter_summaries:
            lines.append(heading)
            lines.append(summary)
            lines.append("")

    else:
        # --- Path B: no chapters — summarize full transcript ---
        print("⚠️  No chapters found — summarizing full transcript as one block")

        summary = summarize_chapter(client, chapter_prompt, "### Full Transcript", transcript)

        print("⏳ Generating TL;DR...")
        tldr = call_groq(client, tldr_prompt + "\n\n" + summary, model="llama-3.1-8b-instant")

        lines = ["## TL;DR", tldr, "", "## Summary", "", summary, ""]

    output = "\n".join(lines)

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ Summary saved to summary.md")
    print("\n--- Preview ---")
    print(output[:600])


if __name__ == "__main__":
    transcript_path = sys.argv[1] if len(sys.argv) > 1 else "transcript.md"
    summarize(transcript_path)