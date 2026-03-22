# Bookfinder General

Research book finder, downloader, processor, and summarizer. Named after the Witchfinder General — except it hunts books, not witches.

## Tech Stack
- Python 3.11+ | Package: `bookfinder_general/`
- `playwright` — browser automation (Cloudflare bypass)
- `pymupdf4llm` — PDF-to-Markdown extraction
- `deep-translator` — auto-translation (Google Translate)
- `fpdf2` — PDF report generation
- `mcp` SDK — MCP server (9 tools)
- `flask` — web UI
- `rich` — CLI
- stop-slop rules embedded in summarizer

## Project Structure
```
bookfinder_general/
  mcp_server.py      # MCP server (9 tools)
  search.py          # Anna's Archive search
  browser.py         # Playwright automation
  download.py        # Download with mirror fallback
  extractor.py       # PDF/EPUB to Markdown
  translator.py      # Auto-translation
  library.py         # Research library management
  summarizer.py      # Summary generation + stop-slop
  pdf_generator.py   # Markdown to PDF
  cli.py             # CLI interface
  config.py          # Configuration
templates/index.html # Web UI
app.py               # Flask server
main.py              # CLI entry
START.bat            # Windows launcher
```

## MCP Tools (9)
search_books, download_book, list_library, read_book, search_book_content,
summarize_book, summarize_topic, save_book_summary, save_research_brief

## Running
- Web: `python app.py` or `START.bat` → http://localhost:5000
- MCP: `python -m bookfinder_general.mcp_server`
- CLI: `python main.py`

## Mirrors (March 2026): .gd, .gl, .pk
## Env: `ANNAS_KEY`, `BOOKFINDER_LIBRARY` (default ~/Research/BookFinder)

## CRITICAL RULES — Read Before Editing

### Never print to stdout
The MCP server uses stdout for JSON-RPC. **Any `print()` without `file=sys.stderr` will corrupt the transport and hang the client.** This caused hours of debugging on 2026-03-22. Every print statement in the entire codebase MUST use `file=sys.stderr`. No exceptions.

### Playwright must stay on its dedicated thread
All Playwright calls go through `_pw_executor` (a single-thread ThreadPoolExecutor) in `browser.py`. Never call Playwright directly from `asyncio.to_thread()` — greenlets are tied to the thread that created them and will crash with "Cannot switch to a different thread."

### Don't use MCP Context for progress
`ctx.report_progress()` can hang if the client doesn't support it. We removed Context entirely. Log progress to stderr with `logger.info()` instead.

### Keep extraction under control
- Files >25MB skip text extraction (likely scanned/image PDFs that hang pymupdf4llm)
- All async steps need `asyncio.wait_for()` timeouts
- Every code path in MCP tools must return JSON, never raise unhandled exceptions

### Dependencies
- Playwright is optional — guarded by `PLAYWRIGHT_AVAILABLE` flag in `browser.py`
- All versions pinned in `requirements.txt` and `pyproject.toml`
- Don't add loose version ranges (`>=`) — pin exact versions (`==`)
