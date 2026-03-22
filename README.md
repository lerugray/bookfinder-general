<div align="center">

# Bookfinder General

**Search. Download. Extract. Translate. Summarize.**

MCP server and research tool. Finds books on Anna's Archive, downloads them, pulls out the text, translates if needed, and writes up summaries. Point Claude at it and ask for a book.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-compatible-00d4ff?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

<br>

*Named after the [Witchfinder General](https://en.wikipedia.org/wiki/Witchfinder_General). Hunts books, not witches.*

</div>

---

> **Legal Disclaimer:** This tool is intended for accessing books and materials you are legally entitled to download. Users are solely responsible for ensuring compliance with applicable copyright laws in their jurisdiction. The authors do not condone or encourage copyright infringement.

---

## What It Does

```
Search query ──> Anna's Archive ──> Download ──> Extract text ──> Translate ──> Summarize ──> PDF Report
                                        │              │              │              │
                                   mirror fallback   Markdown    Google Translate  stop-slop
                                   (LibGen, IPFS)   (pymupdf4llm)  (if non-English)  rules
```

| Feature | Description |
|---------|-------------|
| **Search** | Search Anna's Archive — titles, authors, ISBNs, any language |
| **Download** | Mirror fallback across LibGen, IPFS, Anna's Archive. Validates every file |
| **Extract** | PDF/EPUB to Markdown. Prefers EPUBs (real text). OCR fallback for scans |
| **Translate** | Non-English books auto-translated via Google Translate at download time |
| **Summarize** | Research summaries with [stop-slop](https://github.com/hardikpandya/stop-slop) rules — reads like a person wrote it |
| **PDF Reports** | Cover pages, headings, page numbers. Proper typography |
| **Topic Briefs** | Combine multiple books into one research brief |
| **Library** | Organized collection with metadata, full-text search, git sync |

---

## Quick Start

### Install

```bash
git clone https://github.com/lerugray/bookfinder-general.git
cd bookfinder-general
pip install -e .
```

**Optional extras:**

```bash
pip install -e ".[browser]"    # Browser search (only needed without ANNAS_KEY)
playwright install chromium

pip install -e ".[ocr]"        # OCR for scanned PDFs (RapidOCR)
```

### Use

<table>
<tr>
<td width="50%">

#### Web UI

Double-click **`START.bat`** or run:

```bash
python app.py
```

Opens at [localhost:5000](http://localhost:5000).

</td>
<td width="50%">

#### MCP Server

Add to your Claude Code settings:

```json
{
  "mcpServers": {
    "bookfinder-general": {
      "command": "python",
      "args": ["-m", "bookfinder_general.mcp_server"],
      "cwd": "/path/to/bookfinder-general",
      "env": {
        "ANNAS_KEY": "your_key_here"
      }
    }
  }
}
```

</td>
</tr>
</table>

Then ask Claude:

> *"Find me books about 17th century star fort design"*
>
> *"Download that second result and tell me what it says about defensive geometry"*
>
> *"Summarize the Moltke book, focus on tactical observations about artillery placement"*
>
> *"Create a research brief combining all three books on Italian unification"*

---

## MCP Tools

| Tool | Purpose |
|------|---------|
| `search_books` | Search Anna's Archive with language, format, and content type filters |
| `download_book` | Download + extract text + translate — saves to your research library |
| `read_book` | Read a book's extracted text (returns English translation for foreign books) |
| `list_library` | Browse and filter your research library |
| `search_book_content` | Full-text search across all downloaded books |
| `summarize_book` | Prepare book content with summary instructions and stop-slop rules |
| `summarize_topic` | Prepare multi-book content for topic synthesis |
| `save_book_summary` | Save a generated summary as Markdown + polished PDF |
| `save_research_brief` | Save a cross-book topic brief as Markdown + PDF |

---

## Library Structure

Books are organized in `~/Research/BookFinder/` (configurable):

```
~/Research/BookFinder/
│
├── der-italienische-feldzug-1859-moltke-11ca3de1/
│   ├── original.pdf              # Downloaded file
│   ├── content.md                # Extracted text as Markdown
│   ├── content_en.md             # English translation (if non-English)
│   ├── summary.md                # Research summary
│   ├── summary.pdf               # Polished PDF report
│   └── metadata.json             # Title, author, year, source, etc.
│
└── _topics/
    └── italian-unification-wars/
        ├── summary.md            # Cross-book synthesis
        ├── summary.pdf           # PDF research brief
        └── metadata.json         # Topic metadata + source book IDs
```

---

## How It Works

### Cloudflare Bypass

Anna's Archive sits behind Cloudflare. With an `ANNAS_KEY`, downloads go through their fast API — no browser needed. Without a key, [Playwright](https://playwright.dev/) drives a headless Chromium to get past the challenge. Set `BOOKFINDER_HEADLESS=false` if you need to see the browser window.

### Download Validation

Downloads are checked against magic bytes (`%PDF`, `PK` for EPUBs, etc.) to catch HTML error pages and paywalls. If the fast API fails, falls back to LibGen and other mirrors. Tries multiple download servers and storage paths before giving up.

### Mirror Rotation

Tries `.gd`, `.gl`, `.pk` mirrors in order. Domains rotate due to legal pressure — update `config.py` if they change.

### Text Extraction

Search results are sorted with EPUB first — EPUBs contain real text and always extract cleanly. Large PDFs are often scanned images. [pymupdf4llm](https://github.com/pymupdf/RAG) handles text-based PDFs and EPUBs. For scanned PDFs, install the optional `[ocr]` extra — [RapidOCR](https://github.com/RapidAI/RapidOCR) will automatically kick in when regular extraction comes back empty.

### Translation

Non-English books get translated via [Google Translate](https://github.com/nidhaloff/deep-translator) at download time. Good enough for AI analysis — not publication-grade.

### Library Sync

Set `BOOKFINDER_SYNC=true` to auto-commit and push after each download. Keeps extracted text synced across machines without the large original files. Set up:

```bash
cd ~/Research/BookFinder
git init && git remote add origin git@github.com:you/your-library.git
```

Add `**/original.*` to `.gitignore` to keep the repo lightweight — only extracted text and metadata get pushed.

### Summary Generation

Summaries run through embedded [stop-slop](https://github.com/hardikpandya/stop-slop) rules that strip out AI writing patterns. The output reads like a person wrote it. PDF reports via [fpdf2](https://py-pdf.github.io/fpdf2/) with cover pages, headings, and page numbers.

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANNAS_KEY` | Anna's Archive membership key (**recommended**) | *(none)* |
| `BOOKFINDER_LIBRARY` | Path to your research library | `~/Research/BookFinder` |
| `BOOKFINDER_HEADLESS` | Set to `false` for visible browser window | `true` |
| `BOOKFINDER_SYNC` | Auto-commit library to git after downloads | `false` |

**Anna's Archive membership key** (recommended)

A donation to Anna's Archive (~$5-20) gets you an API key. With it, downloads are fast and don't need Playwright at all:

```bash
# Windows
set ANNAS_KEY=your_key_here

# Linux/Mac
export ANNAS_KEY=your_key_here
```

---

## Tech Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Browser | [Playwright](https://playwright.dev/) | Cloudflare bypass |
| Extraction | [pymupdf4llm](https://github.com/pymupdf/RAG) | PDF/EPUB to Markdown |
| OCR | [RapidOCR](https://github.com/RapidAI/RapidOCR) | Scanned PDF fallback (optional) |
| Translation | [deep-translator](https://github.com/nidhaloff/deep-translator) | Google Translate |
| PDF Reports | [fpdf2](https://py-pdf.github.io/fpdf2/) | Summary PDF generation |
| MCP Server | [MCP SDK](https://modelcontextprotocol.io/) | AI assistant integration |
| Web UI | [Flask](https://flask.palletsprojects.com/) | Browser interface |
| CLI | [Rich](https://github.com/Textualize/rich) | Terminal interface |
| Parsing | [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| Writing Quality | [stop-slop](https://github.com/hardikpandya/stop-slop) | Anti-AI-slop rules (embedded) |

---

## License

MIT — see [LICENSE](LICENSE).

---

🎸 [*Witchfinder General* — Witchfinder General](https://www.youtube.com/watch?v=4bw-G4Ubof8)
