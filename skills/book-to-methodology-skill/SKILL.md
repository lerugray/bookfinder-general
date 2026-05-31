---
name: book-to-methodology-skill
description: "Turn a book in your bookfinder-general library into a reusable skill: a study-skill (frameworks, glossary, on-demand chapters) for any book, or a methodology-skill (a runnable calculator grounded in the book's own numbers) for books with a quantitative model. Use when you want to operationalize a book — not just summarize it — e.g. turn a logistics or formation treatise into an advisor that computes."
allowed-tools:
  - Read
  - Grep
  - Write
  - Bash
argument-hint: <book_id from your library> [skill-name-slug]
---

# Book → Methodology Skill

Convert a bookfinder-general library book into a skill. Two tiers:

- **Study-skill** (any clean book) — frameworks, glossary, on-demand chapter index. *Extract structure, not summaries.*
- **Methodology-skill** (books with a quantitative model) — everything above **plus a calculator** (`scripts/advise.py`) that *carries out* the book's method, with every constant provenance-tagged and a `selftest` that reproduces the book's own worked numbers.

This composes with bookfinder-general: it runs on a library book's `content.md`. The two skills under `../examples/` (`macedonian-logistics-advisor`, `macedonian-phalanx-advisor`) are the canonical templates — read them before generating.

## Step 0 — Locate and health-check the source

Resolve the book's `content.md` (from the MCP tool `prepare_book_for_skill(book_id)`, or `<LIBRARY_DIR>/<book_id>/content.md`). Then **always** run the health probe:

```bash
python3 scripts/extract_health.py "<content.md path>"
```

- `rubble` → **STOP.** It's a scanned-image PDF; tables/formulas didn't survive. Re-acquire as EPUB (bookfinder-general sorts EPUB-first) or re-extract with OCR, then retry. Do not build a calculator from rubble — this is the one failure mode that produces confident-but-fake numbers.
- `degraded` → reference skill OK; build a calculator only from prose-verifiable figures.
- `clean` → proceed to a full methodology-skill.

## Step 1 — Choose the tier

**Methodology-skill** if the book contains a *quantitative model*: rates, formulas, coefficient tables, unit hierarchies, geometry — anything that maps inputs to a computed output (a logistics range, a combat value, a formation frontage). Otherwise a **study-skill**.

## Step 2 — Mine the book (parallel)

Read the actual text (grep/offset, don't dump a 100k-token file). Produce three things:

1. **The model** → `data/<model>.json` — every constant the calculator needs, each as a provenance-tagged cell:
   - `book-stated` — a figure the author adopts.
   - `book-derived` — a figure the author calculates/concludes.
   - `external-sourced` — a number you had to bring from elsewhere (cite it).
   - `missing` — needed but not recoverable.
   Include a `validation` block: the book's *own* worked numbers the `selftest` will reproduce.
2. **The frameworks** → `reference/constraints.md` — the load-bearing principles, framed "the limit is X because Y", each with mechanism + a cited quantitative anchor. Designer-usable, not a book report.
3. **The structure** → `reference/chapters.md` (chapter index) + `glossary.md` (terms). Note if the EPUB scrambled chapter order.

## Step 3 — Write the calculator (methodology-skill only)

`scripts/advise.py` (stdlib only) that reads `data/<model>.json` and exposes:
- compute subcommands (the book's method applied to user inputs);
- a `feasibility` pass that surfaces the book's hard limits as warnings/blockers;
- a `selftest` that **reproduces at least one of the book's own worked figures** within tolerance.

**Hard rules — these are what keep it honest:**
- **Never hardcode a coefficient.** Every number comes from `data/<model>.json` with its provenance.
- **Never invent a number.** If a cell is `missing`, the calculator refuses; if `external-sourced`, it says so.
- **The selftest is the ship gate.** If it can't reproduce a book figure, the calculator does not ship — fall back to a reference skill.

## Step 4 — Write the wrapper files

`SKILL.md` (front-loaded: frontmatter, how-to-use, the procedure, core principles, index), `cheatsheet.md` (at-a-glance tables), `PROVENANCE.md` (book-faithful vs external vs missing; what didn't extract). Match the structure of the two examples exactly — that shared structure is the point.

## Step 5 — Validate and report

```bash
python3 scripts/advise.py selftest   # must PASS
```
Report what was built, the selftest result, and any `external-sourced`/`missing` cells the user should know about.

## Quality rules

1. **Extraction quality decides feasibility.** EPUB → real text → real calculator. Scanned PDF → rubble → reference skill at best. The health probe is not optional.
2. **Provenance over completeness.** A small calculator with every cell cited beats a big one with invented numbers.
3. **Validate against the source.** "Reproduces the book's own worked example" is the difference between a methodology-skill and a plausible fake.
4. **Two tiers, one structure.** Study and methodology skills share the same file layout (`SKILL.md` · `data/` · `scripts/` · `reference/` · `glossary.md` · `cheatsheet.md` · `PROVENANCE.md`). Reuse it.
