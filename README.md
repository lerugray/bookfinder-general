<div align="center">

# Bookfinder General

**Search. Download. Extract. Translate. Summarize.**

An MCP server and web app that finds research books, downloads them, extracts clean readable text, translates foreign languages, and generates polished PDF summaries — all accessible to AI assistants like Claude.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-compatible-00d4ff?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

<br>

*Named after the [Witchfinder General](https://en.wikipedia.org/wiki/Witchfinder_General) — except instead of hunting witches, it hunts books.*

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
| **Search** | Query Anna's Archive in any language — titles, authors, ISBNs, topics |
| **Download** | Automatic mirror fallback across LibGen, IPFS, and Anna's Archive mirrors |
| **Extract** | Convert PDF/EPUB to clean Markdown preserving structure, tables, and headings. EPUBs preferred — always extractable, unlike scanned PDFs |
| **Translate** | Auto-translate non-English books to English (optimized for AI readability) |
| **Summarize** | Generate clean research summaries with [stop-slop](https://github.com/hardikpandya/stop-slop) rules — no AI-sounding prose |
| **PDF Reports** | Polished documents with cover pages, typography, and proper formatting |
| **Topic Briefs** | Synthesize multiple books into a single research brief |
| **Library** | Organized research collection with metadata, full-text search, and tagging |

---

## Quick Start

### Install

```bash
git clone https://github.com/lerugray/bookfinder-general.git
cd bookfinder-general
pip install -e .
```

**Optional — browser-based search** (only needed if you don't have an `ANNAS_KEY`):

```bash
pip install -e ".[browser]"
playwright install chromium
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

Opens at [localhost:5000](http://localhost:5000) — search, browse, download, and manage your library.

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

Then just ask Claude naturally:

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

Anna's Archive uses bot protection. With an `ANNAS_KEY`, downloads go through the fast API and don't need a browser at all. Without a key, [Playwright](https://playwright.dev/) launches a headless Chromium browser to handle Cloudflare challenges automatically. Set `BOOKFINDER_HEADLESS=false` if you need a visible browser window for debugging.

### Download Validation

Every downloaded file is validated with magic byte checking (`%PDF` for PDFs, `PK` for EPUBs, etc.) to ensure you get real files, not HTML error pages or paywalls. If the fast API fails, the tool falls back to browser-based downloading through LibGen and other mirrors. The fast API also iterates multiple download servers and storage paths to find a working source.

### Mirror Rotation

The tool automatically tries multiple mirrors (`.gd`, `.gl`, `.pk`) if one goes down. Domains change periodically due to legal pressure — update the mirror list in `config.py` if needed.

### Text Extraction

Search results are automatically sorted with EPUB first — EPUBs are real text (HTML in a zip) and always extract cleanly, while large PDFs are often scanned images with no extractable text. [pymupdf4llm](https://github.com/pymupdf/RAG) converts PDFs and EPUBs to clean Markdown preserving document structure, tables, lists, and page boundaries. Files over 25MB skip extraction (likely scanned).

### Translation

Non-English books are auto-translated via [Google Translate](https://github.com/nidhaloff/deep-translator) at download time. The translation is optimized for machine readability — accurate enough for AI analysis, not intended for publication.

### Summary Generation

Summaries use embedded [stop-slop](https://github.com/hardikpandya/stop-slop) rules to eliminate AI writing patterns. The result reads like a knowledgeable researcher wrote it, not a language model. PDF reports are generated with [fpdf2](https://py-pdf.github.io/fpdf2/) — styled cover pages, clean typography, proper headings, page numbers.

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANNAS_KEY` | Anna's Archive membership key (**recommended**) | *(none)* |
| `BOOKFINDER_LIBRARY` | Path to your research library | `~/Research/BookFinder` |
| `BOOKFINDER_HEADLESS` | Set to `false` for visible browser window | `true` |

**Recommended: Anna's Archive membership key**

Donating to Anna's Archive (~$5-20) gives you an API key for fast, browserless downloads. With a key, Playwright is not required at all:

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
