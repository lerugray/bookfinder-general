---
name: macedonian-logistics-advisor
description: "Logistic and movement advisor built from Donald Engels, Alexander the Great and the Logistics of the Macedonian Army (1978). Computes daily/march grain-water-forage requirements, pack-animal counts, operational range from a depot, and desert-crossing feasibility for an ancient army; explains Engels's supply constraints. Use when designing or adjudicating army supply/movement (wargame rules, campaign planning, what-if marches) or when reasoning about pre-modern logistics."
allowed-tools:
  - Read
  - Grep
  - Bash
argument-hint: [a force + march to advise on, a logistics question, or "selftest"]
---

# Macedonian Logistics & Movement Advisor
**Source:** Donald W. Engels, *Alexander the Great and the Logistics of the Macedonian Army* (1978) · **Model:** Engels's consumption-vs-carrying supply model

This skill *carries out* Engels's logistics method, it does not just explain it. The script `scripts/advise.py` is the source of truth for every number — its rates live in `data/rates.json`, each cell cited to the book. **Never do the supply arithmetic by hand; run the script.** The book's master tables (Appendix 5) did not survive extraction, so all figures come from its narrative — see `PROVENANCE.md`.

## How to use this skill

- **Advise on a march** — gather the force + the route conditions, then run `advise.py compute`. Report requirements, pack-animal count, range, and any feasibility blockers.
- **Answer a constraints question** (e.g. "why couldn't Alexander cross the Gedrosian desert?") — read `reference/constraints.md`, cite the rule.
- **Look up a number** — `cheatsheet.md` (at-a-glance tables) or `advise.py rates`.
- **Browse the book** — `reference/chapters.md` (chapter index), `glossary.md` (terms).
- **Trust check** — `advise.py selftest` reproduces Engels's own pack-animal figures.

## The advisory procedure (what `compute` runs)

Gather inputs from the user FIRST, then invoke the script.

### Step A — Force composition
Ask for counts of: **soldiers/followers, cavalry horses, pack mules, camels, elephants.** (Followers count as soldiers for consumption — Engels uses ~1 follower per 3 combatants before Gaugamela, 1 per 2 after.)

### Step B — March
Ask for: **days** of march between resupply points, and the **terrain supply state**:
- `grain_only` — water + forage found locally; only grain carried (limit ~10 da practical)
- `normal` — water found locally; grain + forage carried (limit ~7 da)
- `desert` — nothing available; grain + forage + water carried (**hard limit 4 da**)

### Step C — Run it
```bash
python3 scripts/advise.py compute --soldiers 30000 --horses 5000 --mules 6000 --days 10 --terrain normal
# or, for a saved scenario:
python3 scripts/advise.py compute --scenario engagement.json
```

### Step D — Interpret
Report from the JSON: daily grain/water/forage (and water in tons — it dominates), the total for the march, **pack animals needed to self-carry the grain** (this number explodes near the terrain's day-limit), the **operational radius from a depot**, and any `warnings`/`blockers`. If `blockers` is non-empty the march is physically impossible at any herd size — tell the user *why* (cite the constraint) and what unlocks it (fleet, advance depots, splitting the army, waiting for harvest).

---

## Core constraints (the model in six rules)

Full version with mechanisms + citations in `reference/constraints.md`. In brief:

1. **~10-day self-carry limit.** A pack animal eats its own cargo (20 lb/day of 250), so the herd to carry more food *explodes* — 1,121 animals for 1 day's grain, 40,350 for 15, 107,600 for 20. Practical ceiling ~10 days grain, 14 absolute. **Operational radius from a depot = (carried days ÷ 2) × march rate.**
2. **Water binds in arid terrain.** It has a hard floor (2 qt/man) food doesn't, and is ~10× heavier per day. Full-desert crossing limit: **4 days**, nothing more, at any herd size.
3. **Pack animals beat carts; convoys defeat themselves.** Overland resupply is economic only within **60–80 mi** of a depot — beyond that the convoy eats more than it delivers.
4. **Fleet, depots, and requisition do the rest.** A ship carries 400 tons vs a pack animal's 200 lb. Navigable water removes the carried-days cap along that edge; depots depend on local surrender.
5. **The harvest clock gates everything.** No surplus to requisition before harvest, so start dates carry a hidden ration cost = (days to local harvest) × consumption.
6. **Size ↔ route ↔ survivability are coupled.** Consumption and column length scale with army size; water points and pass width don't — so **big armies are *less* survivable** on arid, narrow routes. Split the stack.

---

## Index

| Need | File |
|---|---|
| Compute a march | `scripts/advise.py` (+ `data/rates.json`) |
| At-a-glance tables | `cheatsheet.md` |
| The constraints, with mechanisms + citations | `reference/constraints.md` |
| Chapter-by-chapter | `reference/chapters.md` |
| Term definitions | `glossary.md` |
| What's book-faithful vs. not | `PROVENANCE.md` |

## Scope & limits
This is a faithful implementation of Engels's *narrative* model (the Appendix 5 tables didn't extract — `PROVENANCE.md`). It advises on ancient pre-mechanized land logistics: grain/water/forage, pack animals, march rates, depot range, desert limits. It is an **agent-consulted design/planning tool**, not a runtime engine — for a game loop, port the formulas. It does not model combat, naval logistics in detail, or post-classical supply.
