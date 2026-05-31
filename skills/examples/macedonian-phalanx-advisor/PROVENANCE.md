# Provenance & Limits

**Source:** Taylor, *The Macedonian Phalanx: Equipment, Organization and Tactics from Philip and Alexander to the Roman Conquest* (Pen & Sword, 2020), acquired and extracted via `bookfinder-general` from a clean ~1.16 MB EPUB → `content.md` (14,211 lines, 0% garbage). Line citations (`L####`) refer to that file.

## What is book-faithful vs. not
The whole skill is built from Taylor's text, which extracted cleanly. Unlike a scanned PDF, the EPUB preserved every figure in prose, so the spacing intervals, file depths, sarissa lengths, projection scale, and unit hierarchy are all directly cited.

The numbers ultimately come from **four ancient drill manuals + Polybius**, which Taylor reports *and frequently disputes*:
- **Asclepiodotus** (~100 BC, earliest) — the intervals (4/2/1 cubits, Ascl. 4.1), the file-doubling table (Ascl. 2), supernumeraries.
- **Aelian, Arrian** — later copies of the same Hellenistic tradition.
- **Polybius 18.28–32** — the only *contemporary* historian: the 3-ft man, the 14-cubit sarissa, the five projecting ranks, the 2-against-1 frontage.

## Provenance tags in `data/model.json`
- `tacticians` — a drill-manual figure (Asclepiodotus/Aelian/Arrian).
- `polybius` — from the contemporary historian.
- `taylor-note` — Taylor's caveat, rounding, or dispute.

## Taylor's disputes (carried into the model as caveats)
1. **One-cubit synaspismos** — whether a pike-armed phalanx could really close to 1 cubit is debated (Matthew calls it "impossible"; Taylor calls *that* "wholly untenable" and trusts the sources that it was possible at least on the defensive — "we don't know exactly how it was done"). Polybius **never** uses the 1-cubit order in any calculation.
2. **"Synaspismos" in literary accounts** usually just means generic "close order," not the technical half-metre spacing.
3. **Sarissa chronology** — Taylor rejects dating length-changes from the tacticians (textual corruption, not real period variation); only firm trend is Polybius's 16→14-cubit reduction.
4. **Arrian's "16 feet" / "2 feet"** are treated as copyist errors for *cubits*.
5. **Broken-ground incapacity** (Polybius) is **overstated** per Taylor — the phalanx could fight on imperfect ground, just at a disadvantage.

## Practical caveat
Intervals were judged by eye/body (arm on neighbour's shoulder ≈ 2 cubits; shoulder-to-shoulder ≈ 1 cubit), **never measured with sticks** — treat all cubit figures as ± and the outputs as order-of-magnitude formation geometry, not survey data. The cubit itself is rounded 45 cm → 50 cm for clean conversion.

## Not modelled here
Cavalry organisation (*ile/hipparchia*), full Roman maniple/legion structure, and the detailed countermarch/drill mechanics — present in the book but outside the formation-geometry scope.

## Validation
`scripts/advise.py selftest` reproduces three of the book's own worked figures: the syntagma (256 = 16×16), Polybius's projecting ranks (14-cubit sarissa → 10/8/6/4/2 cubits, five ranks), and the standard 16,000-man phalanx (1,000 files → 1,000 m frontage, 16 m deep) — confirming the calculator's geometry matches the text.
