# bookfinder-general — Autobot Contract

> Bot-scope contract for GeneralStaff-managed cycles, registered
> 2026-04-20. Complements the regular `CLAUDE.md` (which applies
> whenever any Claude Code session touches this repo). This file is
> specifically the briefing an *autonomous* cycle reads before
> picking a task from `tasks.json`.

## What Bookfinder is

Python 3.11+ research tool. MCP server + Flask web UI + CLI. Hunts
books on Anna's Archive, downloads them via Playwright browser
automation, extracts text (PDF / EPUB), translates if needed,
summarizes with stop-slop rules embedded in the summarizer. Exposes
9 tools to calling LLMs via MCP.

Repo: `github.com/lerugray/bookfinder-general` (public, 1 star as of
2026-04-20).

## Hammerstein framing

Bookfinder is named by a user whose name rhymes with "Ray." The
autonomous-bot scope here follows Hammerstein's officer typology as
applied across Ray's portfolio (see
`../generalstaff/docs/internal/` and `catalogdna/docs/internal/AI
Collaboration Principles.md` for the canonical version):

**Industriousness without judgment is *worse* than laziness without
judgment — the damage compounds.** Bots are naturally industrious;
the dispatcher's job is to aim them at work where industriousness
compounds *positively* (correctness work — "right" is well-defined,
tests can verify, diffs are legible) and keep them off work where it
compounds *negatively* (creative / strategic work — the bot will
produce confident slop that looks plausible but is wrong in ways
that don't show up in tests).

Two quadrants matter for this project:

- **Correctness work (bot-safe):** type hints, docstrings, test
  expansion, error-path hardening, refactors with clear specs, bug
  fixes with minimal-repro tests.
- **Creative work (opt-in per `RULE-RELAXATION-2026-04-20.md`):**
  README section drafts, launch post drafts, MCP tool usage
  examples, feature blurbs. **Drafts only** — human review is
  mandatory before publication; bot never writes directly to
  `README.md` or any user-facing surface.

Taste calls (product direction, pricing, MCP tool surface design,
Anna's Archive legal posture, Playwright threading decisions)
**stay with Ray** regardless of whether a task is tagged creative
or correctness.

## Scope for the autonomous bot

**The bot SHOULD do:**
- Correctness work on bounded tasks listed in `state/bookfinder-general/tasks.json`.
- Expand the pytest suite seeded by bf-001.
- Add type hints to modules that lack them (`config.py`,
  `library.py`, `cli.py`).
- Add PEP 257 docstrings to public functions.
- Harden error paths per the "every code path returns JSON, never
  raises" CLAUDE.md rule.
- Small refactors with clear inputs and outputs.
- **Draft creative prose into `drafts/`** (and only there) when the
  task is tagged `creative: true` — Ray reviews and publishes.

**The bot SHOULD NOT do:**
- Invent product features. The MCP tool surface is Ray's to design.
- Change dependency versions. Strict pinning is a CLAUDE.md
  critical rule.
- Touch the Playwright threading model. The dedicated-thread
  invariant in `browser.py` is a CLAUDE.md critical rule.
- Touch MCP stdout discipline. `mcp_server.py`'s "stdout = JSON-RPC,
  no stray `print()`" is a CLAUDE.md critical rule.
- Remove the relevance-ranking step in `search.py`.
- Modify files listed in `hands_off.yaml`.
- Opine on Anna's Archive legal/compliance posture.
- Publish creative drafts directly. `drafts/` is the only sink.

These are Ray's decisions. The bot proposes (correctness work); Ray
disposes (product direction) — and the verification gate catches
structural violations regardless of task category.

## Tech stack

- **Language:** Python 3.11+
- **Detected:** Python package (pyproject.toml, requirements.txt)
  with strict `==` version pinning
- **Verify command:** `python -m pytest tests/ -q && python -m ruff check bookfinder_general/ tests/`
- **Engineer command:** `bash engineer_command.sh ${cycle_budget_minutes}`
- **Branch:** `bot/work` (correctness) or `bot/creative-drafts` (creative)
- **Default branch:** `main` (not master — this predates Ray's
  switch to master on newer projects)

## Hands-off surface

See `hands_off.yaml` in this repo for the local list, and GeneralStaff's
`projects.yaml` §bookfinder-general for the authoritative dispatcher
version (the two are kept in sync by convention — updates go to
both). The "why" for the load-bearing items:

- `bookfinder_general/browser.py` — Playwright must run on a
  dedicated thread; violation deadlocks the MCP server.
- `bookfinder_general/mcp_server.py` — stdout is JSON-RPC. Any
  stray `print()` breaks the MCP protocol silently.
- `bookfinder_general/summarizer.py` — stop-slop rules embedded
  here. Don't "clean up" by removing them.
- `bookfinder_general/search.py` — the relevance-ranking step
  separates "book user asked for" from "book with matching title
  word", and is load-bearing for product quality.
- `pyproject.toml` / `requirements.txt` — strict pinning. Version
  bumps are always a brief-worthy decision, never incidental.
- `CLAUDE.md` / `README.md` — load-bearing rules + user-facing
  copy respectively.

## Creative-work opt-in

Bookfinder is the first managed project with
`creative_work_allowed: true` in GeneralStaff's `projects.yaml`.
See `../generalstaff/docs/internal/RULE-RELAXATION-2026-04-20.md`
for the policy, guardrails, and exit criteria.

Short version of the guardrails:
1. The `creative: true` task flag must be explicit.
2. Drafts land in `drafts/` — never on a user-facing surface.
3. CREATIVE_WORK warning is logged in PROGRESS.jsonl for every
   creative cycle so auditors can grep them.
4. Voice references in `voice_reference_paths` (PIH manuals for
   now; Ray's FB corpus later once raybrain ingests it) calibrate
   the bot's output to Ray's actual voice instead of LLM default.
5. Taste calls (brief, audience, thesis, length band) stay with
   Ray; the bot executes briefs, never generates them.

## How to add work

Append to `state/bookfinder-general/tasks.json` (in the GeneralStaff
repo, not in this repo). Each task:

```json
{
  "id": "bf-NNN",
  "title": "<specific action>",
  "status": "pending",
  "priority": 1,
  "expected_touches": ["path/to/file.py"]
}
```

For creative tasks, add `"creative": true`. Keep titles specific:
file paths, function names, assertions. Vague titles produce scope
drift; specific titles produce clean commits.

## Evaluation criteria

- **Zero hands-off violations merged to main.** The dispatcher's
  rollback must hold when the bot hits a hands-off file.
- **Verified-rate ≥ 70%** on correctness cycles (matches the
  GeneralStaff dogfood baseline).
- **Scope-drift rate ≤ 10%** — reviewer catches attempts to expand
  beyond task spec more than 90% of the time.
- **Average correctness cycle duration ≤ 15 min** — budget is 30,
  should finish well under.
- **≥ 5 consecutive clean verification cycles** before auto_merge
  is considered (Hard Rule 4).
- **Creative drafts Ray can usably edit** — ≤ 2x rewrite effort vs.
  writing from scratch. If 3+ consecutive creative cycles miss this
  bar, revert `creative_work_allowed: false` per RULE-RELAXATION
  guardrails.
- **No un-reviewed public posts.** The bot never publishes a
  creative draft directly. Any occurrence is an immediate revert.
