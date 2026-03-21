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
