# Session Notes

## 2026-03-25 — MCP startup fix (two rounds)

### Issue (round 1)
BookFinder General MCP server failed to load — `python` not found in PATH when
Claude Code spawns the subprocess. Fixed by using full path `C:\Python314\python.exe`.

### Issue (round 2)
Server still not connecting. Server itself works fine (stdio transport, proper
handshake, all 9 tools advertised). Real root cause: `.mcp.json` had **unescaped
Windows backslashes** in JSON strings. `\b` was parsed as backspace, `\r` as
carriage return, etc. — garbling the command and cwd paths before they reached
the OS.

### Fix
Changed paths in `.mcp.json` from backslashes to forward slashes:
- `"C:\\Python314\\python.exe"` → `"C:/Python314/python.exe"`
- `"C:\\Users\\rweis\\OneDrive\\Documents\\bookfinder-general"` → `"C:/Users/rweis/OneDrive/Documents/bookfinder-general"`

Windows accepts forward slashes in paths, and they don't need JSON escaping.

### Other Notes
- Python 3.14.3 installed at C:\Python314
- MCP SDK version: 1.26.0
- Server import takes ~1s, validation ~2s total — within timeout limits
- The `rapidocr_onnxruntime` warning at startup is harmless (OCR optional)
- All 20+ books still in library at C:\Users\rweis\Research\BookFinder\

### Still Needed (from last session)
- The Campaigns of Napoleon — David Chandler (1966, 1100pp) — ISBN 0025236601
- Don Quixote — full English translation
- SPI "Wargame Design" (1977) — not on Anna's Archive, physical only

---

## 2026-03-22 — Debugging, hardening, library buildout

### Current State
Everything working and hardened. 20 books in shared library, private repo set up
for cross-machine access. GitHub repos:
- https://github.com/lerugray/bookfinder-general (public, 22 commits)
- https://github.com/lerugray/bookfinder-library (private, text + metadata only)

### Bugs Found & Fixed

1. **stdout corruption (ROOT CAUSE of MCP hangs)**: `library.py` had `print()` to
   stdout instead of stderr. MCP uses stdout for JSON-RPC — corrupted transport,
   client hung waiting for response that never came. Also fixed in `app.py`.

2. **Greenlet threading crash**: Playwright greenlets tied to creating thread,
   `asyncio.to_thread()` dispatches to random pool threads. Fixed with dedicated
   single-thread `ThreadPoolExecutor` for all Playwright calls.

3. **Browser opening unnecessarily**: Detail page always scraped even when fast API
   had a URL. Fixed to skip browser when API succeeds.

4. **Chromium window spam**: Browser fallback tried every link (25+ windows).
   Capped at 2, Z-Library skipped (requires login).

5. **No timeouts**: Added to every step (search 120s, links 120s, download 180s,
   extraction 300s).

6. **Non-PDF rejection**: Extension defaulted to "pdf" so valid epub/azw3 failed
   magic byte validation. Now passes actual format from search.

7. **networkidle hang**: Changed to `domcontentloaded` with 8s Cloudflare wait.

8. **MCP Context.report_progress hang**: Removed entirely. Log to stderr instead.

9. **Large file extraction hang**: 25MB+ files skip extraction (likely scanned).

### Hardening Pass

**Phase 1 — Critical:**
- stdout leaks fixed (app.py, library.py)
- Browser defaults headless=True (env override BOOKFINDER_HEADLESS=false)
- Playwright import guarded — clear error if missing
- atexit cleanup for browser + ThreadPoolExecutor
- Book IDs capped at 70 chars (Windows MAX_PATH)
- All dependency versions pinned
- MOBI magic bytes fixed (offset 60)

**Phase 2 — UX:**
- Timestamped logs
- Startup dependency validation
- Partial translation failures reported
- Error responses include suggestion field for LLMs

**Phase 3 — Portability:**
- pyproject.toml with optional [browser] extra
- __main__.py for python -m bookfinder_general
- Playwright optional in search.py
- bookfinder-mcp entry point

### EPUB Preference
Search results now sorted EPUB first. EPUBs are real text (HTML in zip) and always
extract cleanly. Large PDFs are often scanned images. MCP server instructions tell
calling LLMs to prefer EPUB. Significantly reduces failed extractions.

### Private Library Repo
Created https://github.com/lerugray/bookfinder-library (private). Contains extracted
text (content.md) and metadata only — original PDF/EPUB files gitignored (too large,
re-downloadable). Clone on work machine for cross-machine access.

### Books in Library (20)
With extracted text:
- Numbers, Predictions and War — Trevor Dupuy (13.2MB PDF)
- Medieval Cities — Henri Pirenne (9.0MB PDF)
- The Thirty Years War — C.V. Wedgwood (24.7MB PDF)
- Military Experience in the Age of Reason — Christopher Duffy (17.3MB PDF)
- Dhalgren — Samuel R. Delany (2.4MB PDF)
- Antigonos the One-Eyed — Richard A. Billows (5.7MB PDF)
- On the Napoleonic Wars: Collected Essays — Chandler (12.4MB PDF)
- Infantry Attacks — Erwin Rommel (9.0MB PDF)
- The Society of the Spectacle — Guy Debord (0.8MB PDF)
- The Red and the Black — Stendhal (24.5MB PDF)
- Don Quixote (Spanish selections) — Cervantes (12.1MB PDF)
- The Collected Works of HP Lovecraft (7.4MB PDF)
- Principia Discordia (x2 copies)
- On War — Clausewitz (from earlier session)
- Cambridge History of Hellenistic Philosophy (text from scanned, partial)
- Thomas Müntzer — Andrew Drummond

Without text (scanned/too large):
- Historical Dictionary of the French Second Empire (54.2MB)
- The Great War at Sea 1914-1918 (66.7MB)
- Jena 1806: Napoleon Destroys Prussia — Chandler/Osprey (52.8MB)

### Still Needed
- The Campaigns of Napoleon — David Chandler (1966, 1100pp) — searches keep
  finding other Chandler books, need ISBN 0025236601
- Don Quixote — full English translation (got Spanish study edition)
- SPI "Wargame Design" (1977) — confirmed not on Anna's Archive, physical only

### API Status
ANNAS_KEY: REDACTED_KEY
Downloads used today: ~17, daily limit: 50

### Key Technical Decisions
- Playwright headless by default (headed caused window spam)
- Dedicated Playwright thread (ThreadPoolExecutor max_workers=1)
- Text extraction inline with 300s timeout (background didn't work in MCP)
- Skip extraction on files >25MB
- Fast API iterates path_index 0-2 × domain_index 0-2 (9 combos)
- Fatal API errors bail immediately to fallbacks
- EPUB preferred over PDF in search results
- Private library repo: text + metadata only, originals gitignored

### Future: OCR for Scanned PDFs
Researched options. Best: OCRmyPDF (needs Tesseract + Ghostscript system deps)
or RapidOCR (pure pip, uses PaddleOCR models via ONNX). Would add as optional
[ocr] extra. 15-30 min processing per large book. Details in memory.

### Working Mirrors (March 2026)
- annas-archive.gd (primary)
- annas-archive.gl
- annas-archive.pk
