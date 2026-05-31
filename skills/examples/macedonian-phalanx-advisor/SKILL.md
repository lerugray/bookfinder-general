---
name: macedonian-phalanx-advisor
description: "Formation-geometry advisor built from Taylor, The Macedonian Phalanx (2020). Computes phalanx frontage, depth, men-to-hold-a-line, sarissa-hedge projection (how many ranks' points reach the enemy), unit breakdown (file -> syntagma -> phalanx), and frontal density vs a Roman line; explains how the phalanx fought and its limits. Use when designing or adjudicating ancient pike/spear formations (wargame rules, scenario setup, what-if deployments) or reasoning about phalanx tactics."
allowed-tools:
  - Read
  - Grep
  - Bash
argument-hint: [a formation to compute, a tactics question, or "selftest"]
---

# Macedonian Phalanx Formation Advisor
**Source:** Taylor, *The Macedonian Phalanx: Equipment, Organization and Tactics* (2020) · **Model:** the ancient tacticians (Asclepiodotus/Aelian/Arrian) + Polybius 18.28–32

This skill *computes* phalanx formation geometry, it does not just describe it. The script `scripts/advise.py` is the source of truth — its constants live in `data/model.json`, each cited to the sources. **Don't do the formation math by hand; run the script.** It validates against the book's own numbers (`advise.py selftest`).

> Companion skill: `macedonian-logistics-advisor` (Engels) models how the same army *moved and ate*; this one models how it *fought*. Same army, same era, two halves of the system.

## How to use this skill

- **Lay out a formation** — give men + depth + order, run `advise.py frontage`. Report frontage, depth, files, and feasibility caveats.
- **Fit a line** — given a frontage to hold, run `advise.py line --length-m L`.
- **The spear hedge** — `advise.py projection --sarissa-cubits 14` → how many ranks' points reach and how far.
- **Order of battle** — `advise.py unit --men N` decomposes into the doubling hierarchy; `--name syntagma` looks one up.
- **Vs Rome** — `advise.py density` → Macedonians-per-Roman and sarissa points faced.
- **Tactics question** — read `reference/constraints.md`, cite the rule. Numbers at a glance: `cheatsheet.md`.

## The advisory procedure

Gather inputs FIRST, then invoke the script.

### Step A — The formation
Ask for: **men**, **depth** (ranks; standard 16, early/hoplite 8, doubled 32), and **order** (`open` 4 cubits/march, `close` 2 cubits/battle, `synaspismos` 1 cubit/locked-shields).

### Step B — Run it
```bash
python3 scripts/advise.py frontage   --men 4096 --depth 16 --order close
python3 scripts/advise.py line       --length-m 1000 --depth 16 --order close
python3 scripts/advise.py projection --sarissa-cubits 14 --grip polybius
python3 scripts/advise.py unit       --men 9000
python3 scripts/advise.py density    --order close
```

### Step C — Interpret
Frontage = (men ÷ depth) × spacing; a 16,000-man phalanx at close order is a 1,000 m × 16 m line. Report the `feasibility` warnings: only ~5 ranks reach (deeper = push/morale, not reach); the line must stay continuous on flat ground; flanks/rear are fatal. For the hedge, give the per-rank projection and the count of reaching ranks.

---

## Core tactics (how it fought, in seven rules)

Full version with mechanisms + citations in `reference/constraints.md`. In brief:

1. **Mass over skill** — the formation is the combat atom; the sarissa is driven by the file's weight, not arm-thrust. Once the block breaks, the phalangite is the *worst* heavy infantryman.
2. **The hedge** — ~5 ranks' points project per front-man (descending 10/8/6/4/2 cubits), giving ~10 sarissae per opposing Roman.
3. **Depth ≠ reach** — only the first ~5 of 16 ranks fight; the rest buy push, morale, and replacements. >16 ranks was thought useless for pushing.
4. **Flanks / rear / gaps are fatal** — one continuous line, no reserves, faces only forward; any gap (terrain, casualties, uneven advance) or flank attack decides the battle (Cynoscephalae, Pydna).
5. **Three orders** — open 4 cubits (march), close 2 cubits (battle), *synaspismos* 1 cubit (locked-shields defence). The mass advance is the win condition.
6. **Combined arms** — hypaspists/peltasts as the hinge, cavalry on the wings; the phalanx is the anvil, not a standalone army (Magnesia: a phalanx "denuded of cavalry" is surrounded and shot down).
7. **Command is coarse** — drill is atomic at file level but army control is wing-level; a sub-commander's initiative can open a fatal gap.

---

## Index

| Need | File |
|---|---|
| Compute a formation | `scripts/advise.py` (+ `data/model.json`) |
| At-a-glance tables | `cheatsheet.md` |
| The tactics, with mechanisms + citations | `reference/constraints.md` |
| Chapter-by-chapter | `reference/chapters.md` |
| Term definitions | `glossary.md` |
| Sources, disputes, what's faithful | `PROVENANCE.md` |

## Scope & limits
Faithful to Taylor's text (a clean EPUB — see `PROVENANCE.md`); the numbers are the tacticians'/Polybius's idealized figures, judged by eye in reality, so treat outputs as formation geometry (±), not survey data. It covers infantry formation/depth/frontage/sarissa-reach/unit structure and phalanx tactics. It does **not** model cavalry organisation, the legion in detail, casualties, or combat resolution. An **agent-consulted design/planning tool**, not a runtime engine.
