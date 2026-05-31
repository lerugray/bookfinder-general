# Provenance & Limits

**Source:** Donald W. Engels, *Alexander the Great and the Logistics of the Macedonian Army* (Univ. of California Press, 1978), acquired and extracted via `bookfinder-general` from a 1.4 MB EPUB → `content.md` (clean text, 7,461 lines). Line citations (`L####`) in `data/rates.json`, `reference/constraints.md`, etc. refer to that file.

## What is book-faithful vs. not

**Recovered from the book (good):** This skill is built from Engels' *narrative and footnotes*, which extracted cleanly. The consumption rates, carrying capacities, march rates, and operational limits are all stated or derived in the prose and are faithfully cited.

**NOT recovered — Appendix 5 "Statistical Tables":** Tables 1–8 (Daily Grain Requirement; Grain+Forage; Grain+Forage+Water; Army Troop Numbers ×3; March Rates; Bematists' Measurements) were page-image tables that the extractor could **not** OCR — `content.md` shows only the heading and placeholder text there, and the inline "see table 7" references point to data that isn't present. **No master table value is used in this skill.** Where a precise tabulated figure is ever needed, re-OCR the source PDF pages for Appendix 5 and Table 7.

## Provenance tags in `data/rates.json`
- `engels-stated` — a working figure Engels adopts (e.g. 3 lb grain/man/day, 250 lb pack-animal capacity).
- `engels-derived` — a figure Engels calculates or concludes (e.g. the 4-day desert limit, the ~10-day practical self-carry, the ~1:10 ratio).

## Known caveats (carried from extraction)
- Engels works in **Imperial gallons** and **choinices/lb**, not medimnus/artaba.
- Several figures are **ranges**, not points: horse water 5–15 gal (8 avg); horse provisions 20–32 lb; rest day every 5–7 days. The skill uses the midpoint/working value and notes the range.
- The **19.5 mpd** whole-army maximum was fleet-assisted (Sinai) — it is *not* a self-supplied rate.
- **40–50 mpd** applies only to small detached units, never the whole army. Engels explicitly **rejects** the 70-mpd Gedrosia and 40-mpd-with-elephants claims as misreadings — do not use them.

## Validation
`scripts/advise.py selftest` reproduces Engels' own worked self-carry figures (1,121 / 40,350 / 107,600 pack animals for 1/15/20-day grain rations) from the formula in `model_constants`, confirming the calculator's core math matches the book within 1%.
