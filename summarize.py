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
        with open("Keys/groq.txt", "r") as f:
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


def chunk_text(text: str, max_words: int = 2000) -> list[str]:
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
            err_str = str(e).lower()
            # 413 — request too large, no point retrying
            if "413" in str(e):
                raise
            # 503 / overloaded — back off and retry
            if ("503" in str(e) or "over capacity" in err_str) and attempt < retries - 1:
                wait = 30 * (attempt + 1)
                print(f"   ⚠️  Model overloaded — waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
            # Rate limit — back off and retry
            elif "rate_limit" in err_str and attempt < retries - 1:
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

    if len(words) <= 2000:
        # Normal path — chapter fits in one call
        return call_groq(
            client,
            chapter_prompt + "\n\n" + heading + "\n\n" + body,
            model="moonshotai/kimi-k2-instruct"
        )

    # Chapter is too large — chunk it
    chunks = chunk_text(body, max_words=2000)
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


def _normalize_heading(s: str) -> str:
    """Strip markdown heading syntax, numbering, and timestamps for comparison."""
    s = re.sub(r'^#+\s*', '', s)           # strip ### prefix
    s = re.sub(r'^\d+:\s*', '', s)         # strip "1: " numbering
    s = re.sub(r'\[.*?\]\(.*?\)', '', s)   # strip [text](url) links
    return s.strip().lower()


def _heading_match(a: str, b: str) -> bool:
    """Check if two headings are essentially the same after normalization."""
    return _normalize_heading(a) == _normalize_heading(b)


def summarize(transcript_path: str) -> None:
    if not __import__("os").path.exists(transcript_path):
        print(f"❌ File not found: {transcript_path}")
        sys.exit(1)

    api_key = load_api_key()

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    client = Groq(api_key=api_key)
    chapter_prompt = load_prompt("Prompts/ch_prompt.txt")
    tldr_prompt = load_prompt("Prompts/tldr_prompt.txt")

    chapters = parse_chapters(transcript)

    if chapters:
        # --- Path A: video has chapters ---
        total = len(chapters)

        # Batch adjacent small chapters to reduce API calls
        BATCH_WORDS = 1500  # max words per batch (leaves room for prompt)
        batches = []  # each batch: list of chapter dicts
        current_batch = []
        current_words = 0

        for ch in chapters:
            ch_words = len(ch["body"].split())
            # If adding this chapter exceeds limit and batch isn't empty, seal batch
            if current_batch and current_words + ch_words > BATCH_WORDS:
                batches.append(current_batch)
                current_batch = []
                current_words = 0
            current_batch.append(ch)
            current_words += ch_words
        if current_batch:
            batches.append(current_batch)

        batch_count = len(batches)
        print(f"📄 Found {total} chapters → batched into {batch_count} API calls")

        # Summarize each batch in parallel
        batch_results = [None] * batch_count

        def _summarize_batch(idx, batch):
            # Combine all chapters in the batch into one prompt
            combined_heading = " + ".join([ch["heading"].replace("### ", "") for ch in batch])
            combined_body = "\n\n".join([f"{ch['heading']}\n{ch['body']}" for ch in batch])
            label = f"[{idx + 1}/{batch_count}]"
            if len(batch) == 1:
                print(f"⏳ {label} {batch[0]['heading']}")
            else:
                print(f"⏳ {label} {len(batch)} chapters: {combined_heading[:80]}...")
            summary = summarize_chapter(client, chapter_prompt, "", combined_body)
            return idx, summary

        with ThreadPoolExecutor(max_workers=min(3, batch_count)) as pool:
            futures = [pool.submit(_summarize_batch, i, b) for i, b in enumerate(batches)]
            for future in as_completed(futures):
                idx, summary = future.result()
                batch_results[idx] = summary
                print(f"✅ [{idx + 1}/{batch_count}] done")

        # Split batch results back into per-chapter summaries
        chapter_summaries = []
        for batch, batch_summary in zip(batches, batch_results):
            if len(batch) == 1:
                chapter_summaries.append((batch[0]["heading"], batch_summary))
            else:
                # Split the batch summary by ### headings
                parts = re.split(r'(### .+)', batch_summary)
                per_chapter = {}
                for j in range(1, len(parts), 2):
                    heading_text = parts[j].strip()
                    body_text = parts[j + 1].strip() if j + 1 < len(parts) else ""
                    per_chapter[heading_text] = body_text

                for ch in batch:
                    # Try to find matching summary by normalized heading
                    matched = False
                    for resp_heading, resp_body in per_chapter.items():
                        if _heading_match(ch["heading"], resp_heading):
                            chapter_summaries.append((ch["heading"], resp_body))
                            matched = True
                            break
                    if not matched:
                        # Fallback: use the entire batch summary for this chapter
                        chapter_summaries.append((ch["heading"], ""))

        # TL;DR from chapter summaries
        print("⏳ Generating overall TL;DR...")
        combined = "\n\n".join([f"{h}\n{s}" for h, s in chapter_summaries])
        tldr = call_groq(client, tldr_prompt + "\n\n" + combined, model="llama-3.1-8b-instant")

        # Build final markdown
        lines = ["## TL;DR", tldr, "", "## Chapter Summaries", ""]
        for heading, summary in chapter_summaries:
            lines.append(heading)
            # Strip only the first ### line if it duplicates the chapter heading
            summary_lines = summary.split("\n")
            if summary_lines and summary_lines[0].startswith("###"):
                if _heading_match(summary_lines[0], heading):
                    summary = "\n".join(summary_lines[1:]).strip()
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