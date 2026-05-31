#!/usr/bin/env python3
"""Extraction-health probe for book-to-(methodology-)skill.

Given a bookfinder-general `content.md` (or any extracted text), judges whether
the extraction is clean enough to build a skill from — the lesson learned the
hard way on a scanned-image PDF (Dupuy) whose tables OCR'd into rotated noise,
versus a clean EPUB (Engels, Taylor) that extracted as real text.

Outputs JSON: char/word counts, a "garbage" ratio (mangled table/OCR lines),
a table-row ratio, a crude ToC check, and a verdict (clean | degraded | rubble)
with a recommendation. A `rubble` verdict means: re-acquire the book as an EPUB
(bookfinder-general sorts EPUB-first for exactly this reason) or re-extract with
OCR enabled before attempting a skill.

Usage:
  extract_health.py /path/to/content.md
  extract_health.py --json /path/to/content.md   # JSON only (for piping)
"""
import json
import re
import sys
from pathlib import Path


def probe(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"not a file: {path}"}
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines() or [""]
    n = len(lines)

    # "garbage" heuristic: lines dominated by pipes/backticks = mangled tables / OCR fragments
    garbage = sum(1 for line in lines if line.count("|") > 3 or line.count("`") > 2)
    garbage_pct = round(100 * garbage / n, 1)

    # table-row ratio: lines that look like (broken) table rows
    table_rows = sum(1 for line in lines if line.count("|") >= 2)
    table_pct = round(100 * table_rows / n, 1)

    # rotated-OCR signature: long all-caps runs with no vowels in sensible places
    # (e.g. "SHOIGNI ALITVHLAT" = "OPERATIONAL LETHALITY" read upside down)
    weird_caps = len(re.findall(r"\b[A-Z]{5,}\b", text))

    words = len(text.split())
    chars = len(text)
    has_toc = bool(re.search(r"^\s*(?:table of contents|contents)\s*$",
                             text[:40000], re.IGNORECASE | re.MULTILINE))

    if garbage_pct >= 30 or (table_pct >= 50 and chars < 200_000):
        verdict = "rubble"
        rec = ("Extraction is degraded (likely a scanned-image PDF). Re-acquire this "
               "book as an EPUB via bookfinder-general (search sorts EPUB-first), or "
               "re-extract with OCR enabled, BEFORE building a skill. Do not build a "
               "calculator from this text — its tables/formulas did not survive.")
    elif garbage_pct >= 10 or words < 5000:
        verdict = "degraded"
        rec = ("Usable for a reference skill, but quantitative tables may be partial. "
               "Build the calculator only from figures you can verify in the prose; "
               "provenance-tag anything sourced elsewhere.")
    else:
        verdict = "clean"
        rec = ("Clean text — safe to build a full study-skill and, if the book carries "
               "a quantitative model, a methodology-skill with a calculator. Ground every "
               "number in a cited line and validate the calculator against the book's own "
               "worked examples.")

    return {
        "ok": True,
        "path": str(p),
        "chars": chars,
        "words": words,
        "lines": n,
        "garbage_pct": garbage_pct,
        "table_row_pct": table_pct,
        "weird_caps_runs": weird_caps,
        "has_toc": has_toc,
        "verdict": verdict,
        "recommendation": rec,
    }


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    json_only = "--json" in sys.argv
    if not args:
        print("usage: extract_health.py [--json] /path/to/content.md", file=sys.stderr)
        sys.exit(1)
    result = probe(args[0])
    if json_only:
        print(json.dumps(result))
        return
    print(json.dumps(result, indent=2))
    if result.get("ok"):
        print(f"\n  Verdict: {result['verdict'].upper()}  "
              f"(garbage {result['garbage_pct']}%, {result['words']:,} words)", file=sys.stderr)


if __name__ == "__main__":
    main()
