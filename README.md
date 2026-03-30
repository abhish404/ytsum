# ytsum

Summarize any YouTube video from the terminal or directly from your browser via a Chrome extension. Powered by Groq — a typical 10-minute video takes under 20 seconds.

---

## Prerequisites

- **Python 3.10+** must be installed
- A free **Groq API key** — get one at [console.groq.com](https://console.groq.com)
- *(Optional)* A Notion **Public Integration** if you want to export summaries — set one up at [notion.so/my-integrations](https://www.notion.so/my-integrations)

---

## Installation

```bash
git clone https://github.com/abhish404/ytsum
cd ytsum
pip install groq yt-dlp youtube-transcript-api notion-client httpx fastapi uvicorn sse-starlette
```

Add your Groq key:

```bash
mkdir Keys
echo "your_groq_api_key" > Keys/groq.txt
```

---

## Running — Two Ways

### 1. CLI (terminal)

```bash
python main.py https://www.youtube.com/watch?v=...
# or just run and paste when prompted
python main.py
```

Output lands in `summary.md`. At the end you'll be asked if you want to push it to Notion.

### 2. Chrome Extension (local server)

Start the backend:

```bash
python server.py
# or: uvicorn server:app --host 0.0.0.0 --port 8000
```

The server runs at `http://localhost:8000`. The Chrome extension talks to it directly — click the extension on any YouTube video page and it handles the rest. Summaries are saved automatically to a `summaries/` folder as timestamped `.md` files.

---

## How It Works

### CLI pipeline

```
YouTube URL
    │
    ├─ yt-dlp                  → video metadata + chapter timestamps
    └─ youtube-transcript-api  → raw transcript
            (both fetched in parallel)
    │
    ▼
filler.py — strips um, uh, like, you know, basically, literally,
            kinda, sort of, i mean, okay, etc. + removes repeated words
    │
    ▼
summarize.py — if the video has chapters, each chapter is summarized
               in parallel via Groq, then a TL;DR is generated from
               all chapter summaries combined.
               Videos without chapters are summarized as one block.
               Chapters over 5000 words are split into chunks,
               summarized individually, then merged back.
    │
    ▼
summary.md  +  (optional) Notion page
```

**Models used:**
- Chapter summaries → `moonshotai/kimi-k2-instruct`
- TL;DR → `llama-3.1-8b-instant`

Both are on Groq's free tier.

Every run appends an entry to `timings.json` — video title, word count, fillers removed, per-step timing.

### Extension pipeline (server.py)

The server exposes three endpoints:

| Endpoint | What it does |
|---|---|
| `POST /prepare` | Fetches transcript + removes fillers. Returns JSON. |
| `POST /summarize` | Takes a cleaned transcript, streams summarization progress back via SSE, returns the final summary. |
| `POST /summarize-full` | Legacy combined endpoint — full pipeline in one SSE stream. |
| `GET /health` | Returns `{"status": "ok"}`. |

The extension passes your browser's YouTube cookies along with the request so yt-dlp can access age-restricted or member-only videos. The server converts them to Netscape format on the fly and discards the file after use.

---

## Notion Setup (optional)

Notion uses OAuth — you authorize once via the browser and the token is saved for all future runs.

1. Create a **Public Integration** at [notion.so/my-integrations](https://www.notion.so/my-integrations) and set the redirect URI to `http://localhost:3456/callback`
2. Save your credentials:

```bash
echo '{"client_id": "...", "client_secret": "..."}' > Keys/notion_oauth.json
```

On first use, a browser window opens for authorization. After you approve, `Keys/notion_token.json` is saved and future runs skip the browser step. You'll be prompted to pick which Notion page to nest the summary under.

---

## Prompts

The AI prompts live in the `Prompts/` folder:

- `Prompts/ch_prompt.txt` — instructions for per-chapter summarization
- `Prompts/tldr_prompt.txt` — instructions for the overall TL;DR

Edit these to change the output format, level of detail, or tone of the summaries.

---

## Keys folder

```
Keys/
├── groq.txt              ← Groq API key (plain text)
├── notion_oauth.json     ← Notion client_id + client_secret
└── notion_token.json     ← auto-created after first OAuth login
```

The `Keys/` directory is in `.gitignore`. Don't commit it.
