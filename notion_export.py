#!/usr/bin/env python3
"""
Notion Export — push summary.md to Notion as native blocks.

Requires:
    pip install notion-client
    Save your Notion Integration Token in notion.txt
    Share target Notion page(s) with the integration
"""

import sys
import re
from notion_client import Client


def load_notion_token() -> str:
    """Load Notion integration token from notion.txt."""
    try:
        with open("Keys/notion.txt", "r") as f:
            token = f.read().strip()
    except FileNotFoundError:
        print("❌ notion.txt not found — create it and paste your Notion Integration Token.")
        print("   Get one at: https://www.notion.so/my-integrations")
        sys.exit(1)
    if not token:
        print("❌ notion.txt is empty — paste your Integration Token inside it.")
        sys.exit(1)
    return token


# ── Rich text helpers ──────────────────────────────────────────────

def _text(content: str, link: str | None = None, bold: bool = False, 
          italic: bool = False, code: bool = False) -> dict:
    """Build a single rich_text object."""
    rt = {
        "type": "text",
        "text": {"content": content, "link": {"url": link} if link else None},
        "annotations": {
            "bold": bold, "italic": italic, "strikethrough": False,
            "underline": False, "code": code, "color": "default",
        },
    }
    return rt


def _parse_inline(text: str) -> list[dict]:
    """Parse inline markdown (links, bold, code) into rich_text array."""
    rich_texts = []
    # Pattern: [label](url), **bold**, `code`
    pattern = r'(\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`)'
    last_end = 0
    for match in re.finditer(pattern, text):
        # Add plain text before this match
        if match.start() > last_end:
            plain = text[last_end:match.start()]
            if plain:
                rich_texts.append(_text(plain))
        if match.group(2) and match.group(3):
            # Link: [label](url)
            rich_texts.append(_text(match.group(2), link=match.group(3)))
        elif match.group(4):
            # Bold: **text**
            rich_texts.append(_text(match.group(4), bold=True))
        elif match.group(5):
            # Code: `text`
            rich_texts.append(_text(match.group(5), code=True))
        last_end = match.end()
    # Remaining plain text
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            rich_texts.append(_text(remaining))
    # Fallback if nothing was parsed
    if not rich_texts:
        rich_texts.append(_text(text))
    return rich_texts


# ── Block builders ─────────────────────────────────────────────────

def _heading2(text: str) -> dict:
    return {"type": "heading_2", "heading_2": {"rich_text": _parse_inline(text), "color": "default"}}


def _heading3(text: str) -> dict:
    return {"type": "heading_3", "heading_3": {"rich_text": _parse_inline(text), "color": "default"}}


def _numbered_item(text: str, children: list[dict] | None = None) -> dict:
    block = {
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": _parse_inline(text), "color": "default"},
    }
    if children:
        block["numbered_list_item"]["children"] = children
    return block


def _callout(text: str, emoji: str = "⭐") -> dict:
    return {
        "type": "callout",
        "callout": {
            "rich_text": _parse_inline(text),
            "icon": {"type": "emoji", "emoji": emoji},
            "color": "default",
        },
    }


def _quote(text: str) -> dict:
    return {"type": "quote", "quote": {"rich_text": _parse_inline(text), "color": "default"}}


def _divider() -> dict:
    return {"type": "divider", "divider": {}}


def _paragraph(text: str = "") -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": _parse_inline(text) if text else [], "color": "default"}}


# ── Markdown → Notion blocks converter ─────────────────────────────

def _strip_list_prefix(line: str) -> str:
    """Remove leading '1. ', '2. ', etc."""
    return re.sub(r'^\d+\.\s+', '', line)


def markdown_to_blocks(md: str) -> list[dict]:
    """Convert summary markdown to a list of Notion block objects."""
    lines = md.split('\n')
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines (but add divider between major sections)
        if not stripped:
            i += 1
            continue

        # ## Heading 2
        if stripped.startswith('## '):
            blocks.append(_heading2(stripped[3:]))
            i += 1
            continue

        # ### Heading 3
        if stripped.startswith('### '):
            blocks.append(_heading3(stripped[4:]))
            i += 1
            continue

        # > ⭐ Callout
        if stripped.startswith('> ⭐'):
            callout_text = stripped[4:].strip()
            blocks.append(_callout(callout_text))
            i += 1
            continue

        # > Quote (non-callout)
        if stripped.startswith('> '):
            blocks.append(_quote(stripped[2:]))
            i += 1
            continue

        # Numbered list item (top-level): starts with digit + dot
        if re.match(r'^\d+\.\s+', stripped):
            item_text = _strip_list_prefix(stripped)

            # Collect sub-items (indented numbered items on next lines)
            children = []
            j = i + 1
            while j < len(lines):
                sub = lines[j]
                # Sub-item: starts with whitespace + digit + dot
                sub_match = re.match(r'^[\t ]+(\d+\.\s+.+)', sub)
                if sub_match:
                    child_text = _strip_list_prefix(sub_match.group(1).strip())
                    children.append(_numbered_item(child_text))
                    j += 1
                else:
                    break

            child_blocks = children if children else None
            blocks.append(_numbered_item(item_text, children=child_blocks))
            i = j
            continue

        # Anything else → paragraph
        blocks.append(_paragraph(stripped))
        i += 1

    return blocks


# ── Notion API operations ──────────────────────────────────────────

def list_pages(client: Client) -> list[dict]:
    """List all pages shared with the integration."""
    results = []
    response = client.search(filter={"property": "object", "value": "page"})
    for page in response.get("results", []):
        # Extract page title
        title = "Untitled"
        props = page.get("properties", {})
        if "title" in props:
            title_arr = props["title"].get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
        elif "Name" in props:
            title_arr = props["Name"].get("title", [])
            if title_arr:
                title = title_arr[0].get("plain_text", "Untitled")
        else:
            # Try any property that has type "title"
            for prop in props.values():
                if prop.get("type") == "title":
                    title_arr = prop.get("title", [])
                    if title_arr:
                        title = title_arr[0].get("plain_text", "Untitled")
                    break

        results.append({"id": page["id"], "title": title})
    return results


def select_page(pages: list[dict]) -> dict:
    """Let user pick a page from the list."""
    if not pages:
        print("❌ No pages found. Make sure you've shared at least one page with your integration.")
        sys.exit(1)

    print("\n📚 Pages shared with your integration:\n")
    for idx, page in enumerate(pages, 1):
        print(f"  {idx}. {page['title']}")

    while True:
        choice = input(f"\nSelect page (1-{len(pages)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(pages):
            selected = pages[int(choice) - 1]
            print(f"✅ Selected: {selected['title']}")
            return selected
        print("❌ Invalid choice, try again.")


def create_child_page(client: Client, parent_id: str, title: str, blocks: list[dict]) -> str:
    """Create a child page under parent_id with the given title and blocks."""
    # Notion API limits to 100 blocks per append call
    # First 100 can go in the page creation, rest appended after
    initial_blocks = blocks[:100]
    remaining_blocks = blocks[100:]

    page = client.pages.create(
        parent={"page_id": parent_id},
        properties={"title": [{"text": {"content": title}}]},
        children=initial_blocks,
    )
    page_id = page["id"]

    # Append remaining blocks in batches of 100
    for batch_start in range(0, len(remaining_blocks), 100):
        batch = remaining_blocks[batch_start:batch_start + 100]
        client.blocks.children.append(block_id=page_id, children=batch)

    return page.get("url", page_id)


# ── Main export function ───────────────────────────────────────────

def export_summary(video_title: str, summary_path: str = "summary.md") -> str:
    """Export summary.md to Notion. Returns the Notion page URL."""
    token = load_notion_token()
    client = Client(auth=token)

    # Read summary
    with open(summary_path, "r", encoding="utf-8") as f:
        md = f.read()

    # Pick target page
    print("⏳ Fetching your Notion pages...")
    pages = list_pages(client)
    parent = select_page(pages)

    # Convert and push
    print("⏳ Converting summary to Notion blocks...")
    blocks = markdown_to_blocks(md)
    print(f"   {len(blocks)} blocks to upload")

    print("⏳ Creating Notion page...")
    page_title = f"📹 {video_title}"
    url = create_child_page(client, parent["id"], page_title, blocks)

    print(f"✅ Notion page created: {url}")
    return url


if __name__ == "__main__":
    title = input("Video title: ").strip() or "YouTube Summary"
    export_summary(title)
