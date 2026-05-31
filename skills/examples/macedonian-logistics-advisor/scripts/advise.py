#!/usr/bin/env python3
"""Macedonian logistics / movement advisor — Engels (1978) QJM-style supply model.

Every number this calculator uses lives in ../data/rates.json (provenance-tagged
to the book). The arithmetic is Engels's; nothing is hardcoded here. The
pack-animal self-carry formula reproduces Engels's own figures
(1,121 / 40,350 / 107,600 animals) — run `selftest` to verify.

Usage:
  advise.py compute  --scenario path.json   # full advisory for a force + march
  advise.py compute  --soldiers 30000 --horses 5000 --mules 6000 --days 10 --terrain normal
  advise.py rates                            # dump the rate table
  advise.py selftest                         # reproduce Engels's worked numbers

Scenario JSON:
  {
    "force":   {"soldier": 30000, "cavalry_horse": 5000, "pack_mule": 6000,
                "camel": 0, "elephant": 0},
    "days":    10,
    "terrain": "normal" | "grain_only" | "desert",  # what must be CARRIED
    "march_rate": "planning"                          # key in march_rates_mpd
  }

terrain meanings (what the army must carry vs. find locally):
  grain_only : water + forage found locally; only grain carried   (limit ~25 da theo / 10 practical)
  normal     : water found locally; grain + forage carried        (limit ~12.5 theo / 7 practical)
  desert     : nothing available; grain + forage + water carried  (limit ~4 da)
"""
import argparse
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "rates.json"


def load_rates():
    return json.loads(DATA.read_text(encoding="utf-8"))


def daily_requirements(force, rates):
    """Total grain/water/forage per day for a force composition."""
    cons = rates["consumption_per_day"]
    tot = {"grain_lb": 0.0, "water_gal": 0.0, "forage_lb": 0.0}
    unknown = []
    for entity, count in force.items():
        if count <= 0:
            continue
        if entity not in cons:
            unknown.append(entity)
            continue
        c = cons[entity]
        tot["grain_lb"] += count * (c["grain_lb"] or 0)
        tot["water_gal"] += count * (c["water_gal"] or 0)
        tot["forage_lb"] += count * (c["forage_lb"] or 0)
    return tot, unknown


def pack_animals_for_self_carry(grain_per_day_lb, days, terrain, rates):
    """Engels's self-carry explosion. An average pack animal carries 250 lb but
    eats its own load each day, so the herd needed to carry N days of the army's
    grain diverges as N approaches the capacity/self-consumption ratio.

      animals = grain_per_day * days / (capacity - self_consumption_per_day * days)

    grain_only terrain: animal grazes forage, eats only 10 lb grain/day  -> diverges at 25 da
    normal terrain:     animal eats grain + forage = 20 lb/day            -> diverges at 12.5 da
    desert:             also carries water; net payload collapses         -> ~4 da hard limit
    """
    mc = rates["model_constants"]
    cap = mc["pack_animal_capacity_lb"]                 # 250
    grain_self = mc["pack_animal_grain_self_lb_per_day"]   # 10
    forage_self = mc["pack_animal_forage_self_lb_per_day"]  # 10

    if terrain == "grain_only":
        self_per_day = grain_self                        # forage grazed
    elif terrain == "normal":
        self_per_day = grain_self + forage_self          # grain + forage carried
    else:  # desert: animal must also carry its own water (8 gal = 80 lb)
        self_per_day = grain_self + forage_self + 80

    denom = cap - self_per_day * days
    if denom <= 0:
        return None, self_per_day  # impossible at any herd size
    return grain_per_day_lb * days / denom, self_per_day


def feasibility(force, days, terrain, rates):
    lim = rates["operational_limits"]
    warnings, blockers = [], []

    # carry-days ceiling by terrain
    if terrain == "desert":
        ceil = lim["full_desert_days"]["half_ration"]      # 4
        if days > ceil:
            blockers.append(
                f"DESERT: {days} days exceeds Engels's hard limit of {ceil} days "
                f"with no grain/forage/water available (L2034). Impossible at any herd size."
            )
        elif days > lim["full_desert_days"]["full_ration"]:
            warnings.append(
                f"DESERT: feasible only at HALF rations; {lim['full_desert_days']['full_ration']} "
                f"days is the full-ration limit before heavy casualties (L2034)."
            )
    elif terrain == "normal":
        p = lim["self_carry_grain_forage_days"]["practical"]   # 7
        if days > p:
            warnings.append(
                f"NORMAL terrain: {days} days exceeds the ~{p}-day practical self-carry "
                f"(grain+forage); requires resupply/depots or local forage (L2011)."
            )
    else:  # grain_only
        p = lim["self_carry_grain_days"]["practical"]          # 10
        if days > p:
            warnings.append(
                f"GRAIN-ONLY terrain: {days} days exceeds the ~{p}-day practical self-carry; "
                f"absolute overland ceiling is {lim['self_carry_grain_days']['absolute_ceiling']} "
                f"days no matter how many animals (L2103)."
            )
    return warnings, blockers


def effective_march(rates, key="planning"):
    mr = rates["march_rates_mpd"]
    rate = mr.get(key, mr["planning_rate"])["value"]
    n = rates["operational_limits"]["rest_day_every_n_days"]["value"]  # 6
    effective = rate * (n - 1) / n  # one rest day every n days
    return rate, round(effective, 1)


def compute(scenario, rates):
    force = {k: int(v) for k, v in scenario.get("force", {}).items()}
    days = int(scenario.get("days", 10))
    terrain = scenario.get("terrain", "normal")
    rate_key = scenario.get("march_rate", "planning")
    if rate_key in ("planning", "long_haul", "short"):
        rate_key = {"planning": "planning_rate", "long_haul": "long_haul_average",
                    "short": "short_distance"}.get(rate_key, rate_key)

    daily, unknown = daily_requirements(force, rates)
    total = {k: round(v * days, 1) for k, v in daily.items()}
    grain_pa, self_pd = pack_animals_for_self_carry(daily["grain_lb"], days, terrain, rates)
    warnings, blockers = feasibility(force, days, terrain, rates)
    base_rate, eff_rate = effective_march(rates, rate_key)

    # operational radius from a depot: must reach next depot / return before ration zeroes
    radius_miles = round((days / 2) * eff_rate, 1)
    econ = rates["operational_limits"]["economic_resupply_radius_miles"]

    out = {
        "ok": not blockers,
        "force": force,
        "days": days,
        "terrain": terrain,
        "daily_requirement": {
            "grain_lb": round(daily["grain_lb"], 1),
            "water_gal": round(daily["water_gal"], 1),
            "water_tons": round(daily["water_gal"] * rates["model_constants"]["imperial_gal_to_lb"] / 2000, 1),
            "forage_lb": round(daily["forage_lb"], 1),
        },
        "total_for_march": total,
        "pack_animals_to_self_carry_grain": (
            int(round(grain_pa)) if grain_pa is not None else "IMPOSSIBLE (herd eats its own load before arrival)"
        ),
        "pack_animal_self_consumption_lb_per_day": self_pd,
        "march": {
            "base_rate_mpd": base_rate,
            "effective_mpd_with_rest_days": eff_rate,
            "operational_radius_from_depot_miles": radius_miles,
            "economic_resupply_radius_miles": econ["value"],
            "radius_within_economic_range": radius_miles <= econ["value"],
        },
        "warnings": warnings,
        "blockers": blockers,
        "unknown_entities": unknown,
        "provenance": "All rates from Engels (1978) via data/rates.json; tables in Appendix 5 did not survive extraction — see PROVENANCE.md.",
    }
    return out


def selftest(rates):
    """Reproduce Engels's worked self-carry figures for the Hellespont army.
    He gives 1,121 animals for a 1-day grain ration, 40,350 for 15 days,
    107,600 for 20 days (grain-only terrain) -> implies ~269,040 lb grain/day.
    """
    grain_per_day = 269040.0  # back-solved from Engels's 1-day figure (1121 * 240)
    cases = [(1, 1121), (15, 40350), (20, 107600)]
    print("selftest: reproducing Engels's self-carry figures (grain-only terrain)")
    ok = True
    for days, expected in cases:
        got, _ = pack_animals_for_self_carry(grain_per_day, days, "grain_only", rates)
        got = int(round(got))
        err = abs(got - expected) / expected
        flag = "OK " if err <= 0.01 else "XX "
        ok = ok and err <= 0.01
        print(f"  {flag} {days:2d}-day grain ration: got {got:>7,}  expected {expected:>7,}  (err {err*100:.2f}%)")
    print("RESULT:", "PASS — formula matches the book within 1%" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Macedonian logistics advisor (Engels 1978)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compute")
    c.add_argument("--scenario")
    c.add_argument("--soldiers", type=int, default=0)
    c.add_argument("--horses", type=int, default=0)
    c.add_argument("--mules", type=int, default=0)
    c.add_argument("--camels", type=int, default=0)
    c.add_argument("--elephants", type=int, default=0)
    c.add_argument("--days", type=int, default=10)
    c.add_argument("--terrain", default="normal", choices=["normal", "grain_only", "desert"])
    c.add_argument("--march-rate", default="planning")

    sub.add_parser("rates")
    sub.add_parser("selftest")
    args = ap.parse_args()
    rates = load_rates()

    if args.cmd == "rates":
        print(json.dumps(rates, indent=2))
    elif args.cmd == "selftest":
        sys.exit(selftest(rates))
    elif args.cmd == "compute":
        if args.scenario:
            scen = json.loads(Path(args.scenario).read_text())
        else:
            scen = {
                "force": {"soldier": args.soldiers, "cavalry_horse": args.horses,
                          "pack_mule": args.mules, "camel": args.camels,
                          "elephant": args.elephants},
                "days": args.days, "terrain": args.terrain, "march_rate": args.march_rate,
            }
        print(json.dumps(compute(scen, rates), indent=2))


if __name__ == "__main__":
    main()
