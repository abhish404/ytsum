#!/usr/bin/env python3
"""
Notion Export — push summary.md to Notion as native blocks.

Uses OAuth for authentication:
    First run  → browser opens, user authorizes, token saved
    Later runs → uses saved token from Keys/notion_token.json

Setup:
    1. Create a Public integration at https://www.notion.so/my-integrations
    2. Set redirect URI to http://localhost:3456/callback
    3. Save client_id and client_secret in Keys/notion_oauth.json
"""

import sys
import os
import re
import json
import base64
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx
from notion_client import Client

OAUTH_CONFIG_PATH = "Keys/notion_oauth.json"
TOKEN_PATH = "Keys/notion_token.json"
REDIRECT_URI = "http://localhost:3456/callback"
CALLBACK_PORT = 3456


# ── OAuth flow ─────────────────────────────────────────────────────

def _load_oauth_config() -> dict:
    """Load OAuth client_id and client_secret from config file."""
    if not os.path.exists(OAUTH_CONFIG_PATH):
        print(f"❌ {OAUTH_CONFIG_PATH} not found.")
        print("   Create it with your Notion Public Integration credentials:")
        print('   {"client_id": "...", "client_secret": "..."}')
        print("   Get these at: https://www.notion.so/my-integrations")
        sys.exit(1)
    with open(OAUTH_CONFIG_PATH, "r") as f:
        config = json.load(f)
    if not config.get("client_id") or not config.get("client_secret"):
        print(f"❌ {OAUTH_CONFIG_PATH} is missing client_id or client_secret.")
        sys.exit(1)
    return config


def _save_token(token_data: dict) -> None:
    """Save OAuth token data to disk."""
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)


def _load_saved_token() -> str | None:
    """Load previously saved access token, if it exists."""
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "r") as f:
                data = json.load(f)
            token = data.get("access_token")
            if token:
                return token
        except (json.JSONDecodeError, ValueError):
            print("⚠️  Saved token file is corrupted — will re-authenticate.")
    return None


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Tiny HTTP handler that captures the OAuth callback code."""
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                b"<h1>&#10004; Notion connected!</h1>"
                b"<p>You can close this tab and return to the terminal.</p>"
                b"</body></html>"
            )
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {error}</h1></body></html>".encode())

    def log_message(self, format, *args):
        pass  # Suppress server logs


def _run_oauth_flow() -> str:
    """Run the full OAuth flow: browser → callback → token exchange."""
    config = _load_oauth_config()
    client_id = config["client_id"]
    client_secret = config["client_secret"]

    # Build authorization URL
    auth_url = (
        f"https://api.notion.com/v1/oauth/authorize"
        f"?owner=user"
        f"&client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
    )

    # Start local callback server
    server = HTTPServer(("localhost", CALLBACK_PORT), _OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Open browser
    print(f"🌐 Opening browser for Notion authorization...")
    print(f"   (If it doesn't open, visit: {auth_url})")
    webbrowser.open(auth_url)

    # Wait for callback
    print("⏳ Waiting for authorization...")
    server_thread.join(timeout=120)
    server.server_close()

    code = _OAuthCallbackHandler.auth_code
    if not code:
        print("❌ Authorization timed out or was denied.")
        sys.exit(1)

    print("✅ Authorization code received — exchanging for token...")

    # Exchange code for access token
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = httpx.post(
        "https://api.notion.com/v1/oauth/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )

    if response.status_code != 200:
        print(f"❌ Token exchange failed: {response.text}")
        sys.exit(1)

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        print(f"❌ No access_token in response: {data}")
        sys.exit(1)

    # Save token for future runs
    token_data = {
        "access_token": access_token,
        "bot_id": data.get("bot_id", ""),
        "workspace_name": data.get("workspace_name", ""),
        "workspace_id": data.get("workspace_id", ""),
    }
    _save_token(token_data)
    print(f"✅ Connected to workspace: {token_data['workspace_name']}")
    return access_token


def load_notion_token() -> str:
    """Load saved token or run OAuth flow if needed."""
    token = _load_saved_token()
    if token:
        print("🔑 Using saved Notion token")
        return token
    return _run_oauth_flow()


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

    # Pick target page — with auto-recovery for expired tokens
    print("⏳ Fetching your Notion pages...")
    try:
        pages = list_pages(client)
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "invalid" in str(e).lower():
            print("⚠️  Token expired or revoked — re-authenticating...")
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
            token = _run_oauth_flow()
            client = Client(auth=token)
            pages = list_pages(client)
        else:
            raise

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
    summary_file = sys.argv[1] if len(sys.argv) > 1 else "summary.md"

    if not os.path.exists(summary_file):
        print(f"❌ {summary_file} not found. Run the summarizer first, or pass a path:")
        print(f"   python notion_export.py [summary_file]")
        sys.exit(1)

    title = input("Video title (or press Enter for default): ").strip() or "YouTube Summary"
    url = export_summary(title, summary_path=summary_file)
    print(f"\n🎉 Done! Page: {url}")
