# Session Notes

## 2026-05-31 — Mac setup recovery + Book→Skill feature (v0.2.0)

First substantial session on the Mac (Mac-Neo). Two halves: get BG working
here, then build a new feature on top of it.

### Both MCP servers were dead on the Mac (ENOENT)
Repo is Windows-authored; `.mcp.json` didn't match this machine.
- `bookfinder-general`: `command: "python"` — but this Mac has no `python`,
  only `/opt/homebrew/bin/python3`. And `mcp` + deps were never installed here
  (the `.venv` only had playwright). Two failures stacked.
- `raybrain`: `node` pointing at a `C:/Users/rweis/...` path that can't exist
  on Mac. Windows-only server.

Fixes:
- `.venv/bin/pip install -e ".[browser]"` + `playwright install chromium`
  (Python 3.14; all pins resolved).
- `.mcp.json` `bookfinder-general.command` → absolute `.venv/bin/python`. This
  edit is Mac-specific, so `git update-index --skip-worktree .mcp.json` — it
  never reaches Windows and won't accidentally commit.
- raybrain disabled on Mac via `.claude/settings.local.json`
  (`enabledMcpjsonServers` = just bookfinder-general).
- Verified with a real stdio handshake (all tools advertised).

### Environment recovered
- `ANNAS_KEY` wasn't in any live config here (only a doc placeholder in old
  transcripts). Real key recovered from the PC over the homelab — `ssh home-pc`
  (WSL on DESKTOP-MM0B3G2, Tailscale; Windows files at `/mnt/c`), read from the
  PC's `~/.claude/settings.json`, written to the Mac's `~/.claude/settings.json`
  env block.
- Library: the text-only clone lives at `~/Desktop/Dev Work/bookfinder-library`
  (54 books on the Mac; PC has 81). `BOOKFINDER_LIBRARY` set to it in
  settings.json env. (Default `~/Research/BookFinder` doesn't exist on the Mac.)

### Book → Skill feature (shipped as v0.2.0)
Studied `virgiliojr94/book-to-skill` and assessed forking it for a computational
"methodology-skill" — a skill that *runs* a book's quantitative method, not just
explains it.

Key finding: feasibility is decided by extraction quality. Dupuy's *Numbers,
Predictions and War* is a scanned-image PDF → OCR rubble (appendix tables came
out as rotated noise) → no calculator possible. Clean EPUBs extract as real text
→ they work. Same EPUB-first lesson the search ranking already encodes.

Built two worked examples end-to-end (BG search→download→extract, then generate
the skill):
- `macedonian-logistics-advisor` (Engels) — consumption/range model; selftest
  reproduces Engels's own pack-animal figures (1,121 / 40,350 / 107,600).
- `macedonian-phalanx-advisor` (Taylor) — formation geometry (a deliberately
  *different* computation, to harden the template); selftest reproduces the
  syntagma (256 = 16×16) and Polybius's projecting ranks.

Both share one file layout (`SKILL.md` · `data/<model>.json` · `scripts/advise.py`
with compute+feasibility+selftest · `reference/` · `glossary` · `cheatsheet` ·
`PROVENANCE`). That shared scaffold is the extractable generator.

Productized → PR #1 → merged → **v0.2.0** (GitHub release cut):
- `skills/book-to-methodology-skill/` — generator recipe + `extract_health.py`
  (the clean/degraded/rubble probe).
- `skills/examples/` — the two advisors as living templates.
- 10th MCP tool `prepare_book_for_skill(book_id)` — health-checks a book and
  hands the agent content + recipe; generation stays agent-side, NOT in the
  server (preserves the stdout-is-JSON-RPC discipline).
- README "Book → Skill" section; tool count 9→10; version 0.1.0→0.2.0.
- pytest 4/4, ruff clean (package + skills).

### Key decisions / notes
- Generator deliberately lives OUTSIDE the MCP Python package (different
  lifecycle; the server is reserved for search/download/library + its hard
  stdout rule). It composes with BG: BG makes `content.md`, the recipe consumes it.
- Methodology-skill honesty gate: every coefficient is provenance-tagged, and
  the calculator's selftest must reproduce the book's own worked numbers or it
  doesn't ship.
- On the Mac, `python` isn't on PATH — use `.venv/bin/python` (or `python3`).

---

## 2026-03-25 — MCP portability overhaul

### Cross-machine portability fixes
The root problem: hardcoded absolute paths in `.mcp.json` broke every time
switching between home (rweis) and work (different username) machines.

**What changed:**
- `.mcp.json` now uses `"python" + "-m bookfinder_general.mcp_server"` — no
  absolute paths, no `cwd`. Works on any machine with `pip install -e .`
- PIH's `.mcp.json` gitignored (machine-specific config shouldn't be tracked)
- `ANNAS_KEY` moved to `~/.claude/settings.json` env block (per-machine,
  auto-injected into all MCP servers, no more putting it in repo files)
- Key scrubbed from entire git history with git-filter-repo + force-push
- `pyproject.toml` build-backend fixed (`setuptools.build_meta`)
- Added `mcp__bookfinder-general__*` to permissions allow list for don't-ask mode
- README updated with portable setup instructions

### Per-machine one-time setup
1. `git clone` + `pip install -e .`
2. Tell Claude: "Add ANNAS_KEY to my Claude settings.json env. The key is [key]"
3. Tell Claude: "Add mcp__bookfinder-general__* to my permissions allow list"

### MCP startup fix (two rounds)

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
ANNAS_KEY: stored in Claude memory and ~/.claude/settings.json (not in repo)
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
