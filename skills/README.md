# Book → Skill

Turn a book in your bookfinder-general library into a reusable agent skill.

- **[`book-to-methodology-skill/`](book-to-methodology-skill/SKILL.md)** — the generator. A recipe (for Claude Code / any compatible agent) that converts a library book's extracted `content.md` into either a **study-skill** (frameworks, glossary, on-demand chapters) or, for books with a quantitative model, a **methodology-skill** with a runnable calculator whose every number is provenance-tagged and validated against the book's own worked examples. Includes `scripts/extract_health.py`, the extraction-quality probe that decides which is possible.
- **[`examples/`](examples/)** — two finished methodology-skills, built from library books, that serve as the canonical templates:
  - `macedonian-logistics-advisor` — from Engels, *Alexander the Great and the Logistics of the Macedonian Army*. Computes ration/water/forage requirements, pack-animal counts, march range, and desert-crossing feasibility. `selftest` reproduces Engels's own pack-animal figures.
  - `macedonian-phalanx-advisor` — from Taylor, *The Macedonian Phalanx*. Computes frontage, depth, sarissa-hedge projection, unit breakdown, and density vs a Roman line. `selftest` reproduces the syntagma (256 = 16×16) and Polybius's projecting ranks.

## How it fits the pipeline

```
bookfinder-general:  search → download → extract → content.md
                                                       │
        prepare_book_for_skill(book_id)  ──────────────┤  (MCP tool: health-check + hand off)
                                                       ▼
        book-to-methodology-skill recipe → ~/.claude/skills/<your-skill>/
```

The generator runs *on* a library book's `content.md`; it does not live inside the MCP server (which is reserved for the search/download/library tools). Extraction quality is the deciding factor — clean EPUBs become real calculators, scanned-image PDFs do not, which is why the probe runs first and why search sorts EPUB-first.

## Install a generated skill

Generated skills are written to `~/.claude/skills/<slug>/` (Claude Code) and are usable immediately, e.g. `/macedonian-logistics-advisor` or by running `python3 scripts/advise.py …` directly.
