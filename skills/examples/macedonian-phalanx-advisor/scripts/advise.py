#!/usr/bin/env python3
"""Macedonian phalanx formation advisor — Taylor (2020), from the ancient tacticians.

Every number lives in ../data/model.json (provenance-tagged to the book/sources).
The geometry is the tacticians' and Polybius's; nothing is hardcoded here. The
calculator reproduces the book's own worked figures (syntagma 256 = 16x16;
Polybius's five projecting ranks at 10/8/6/4/2 cubits; a 16,000-man phalanx =
1,000 files = ~1,000 m frontage). Run `selftest` to verify.

Usage:
  advise.py frontage --men 4096 --depth 16 --order close
  advise.py line --length-m 1000 --depth 16 --order close
  advise.py projection --sarissa-cubits 14 --grip polybius --order close
  advise.py unit --men 4096          # decompose into the doubling hierarchy
  advise.py unit --name syntagma     # look up a named unit
  advise.py density --order close    # 2-against-1 frontal density vs a Roman
  advise.py model                    # dump the model table
  advise.py selftest                 # reproduce the book's worked numbers

orders: open (4 cubits/2 m, march) | close (2 cubits/1 m, battle) | synaspismos (1 cubit/0.5 m, locked shields)
"""
import argparse
import json
import math
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "model.json"


def load_model():
    return json.loads(DATA.read_text(encoding="utf-8"))


def spacing_m(order, m):
    s = m["spacing_by_order"].get(order)
    if not s:
        raise SystemExit(f"unknown order '{order}'; use open|close|synaspismos")
    return s["metres"], s["cubits"]


def frontage(men, depth, order, m):
    sm, sc = spacing_m(order, m)
    files = men / depth
    return {
        "men": men, "depth_ranks": depth, "order": order,
        "spacing_m_per_man": sm,
        "files": round(files, 1),
        "frontage_m": round(files * sm, 1),
        "depth_m": round(depth * sm, 1),
        "note": "frontage = (men/depth) x spacing; rank interval = file interval, so depth_m uses the same spacing.",
    }


def men_for_line(length_m, depth, order, m):
    sm, sc = spacing_m(order, m)
    files = length_m / sm
    return {
        "line_length_m": length_m, "depth_ranks": depth, "order": order,
        "files_needed": math.ceil(files),
        "men_needed": math.ceil(files) * depth,
        "spacing_m_per_man": sm,
    }


def projection(sarissa_cubits, grip, order, m):
    s = m["sarissa"]
    grip_loss = s["grip_loss_cubits"].get(grip, s["grip_loss_cubits"]["polybius_counterweight"])
    interval = s["rank_interval_cubits"]  # 2 cubits, in BOTH directions
    cubit_m = m["cubit"]["metres"]
    front = sarissa_cubits - grip_loss
    ranks = []
    n = 1
    while True:
        proj = front - interval * (n - 1)
        if proj <= 0:
            break
        ranks.append({"rank": n, "projects_cubits": proj, "projects_m": round(proj * cubit_m, 2)})
        n += 1
    return {
        "sarissa_cubits": sarissa_cubits,
        "sarissa_m": round(sarissa_cubits * cubit_m, 2),
        "grip_model": grip, "grip_loss_cubits": grip_loss,
        "rank_interval_cubits": interval,
        "front_rank_projection_cubits": front,
        "ranks_projecting": len(ranks),
        "per_rank": ranks,
        "note": "Each front-rank man has this many sarissa points ahead of him (his own + the ranks behind). Ranks past the last add push/morale, not reach.",
    }


def decompose_units(men, m):
    """Greedy decomposition into the doubling hierarchy (largest first)."""
    units = sorted(m["unit_hierarchy"], key=lambda u: -u["men"])
    rem = men
    parts = []
    for u in units:
        if rem <= 0:
            break
        k = rem // u["men"]
        if k:
            parts.append({"unit": u["name"], "count": int(k), "men_each": u["men"]})
            rem -= k * u["men"]
    return {"men": men, "breakdown": parts, "remainder_men": int(rem)}


def lookup_unit(name, m):
    name = name.lower()
    for u in m["unit_hierarchy"]:
        if name in u["name"].lower():
            return u
    if name in ("taxis-alexander", "alexander-taxis"):
        return {"name": "taxis (Alexander's literary sense)", "men": m["alexander_taxis_men"],
                "composition": "largest subdivision of Alexander's phalanx (~1,500 men)"}
    return {"error": f"no unit matching '{name}'", "available": [u["name"] for u in m["unit_hierarchy"]]}


def density(order, m):
    sm_mac, _ = spacing_m(order, m)
    sm_rom = m["spacing_by_order"]["open"]["metres"]  # Roman swordplay ~ open order (6 ft)
    macs = sm_rom / sm_mac                            # ~2 Macedonians per Roman at close order
    points = round(macs) * m["sarissa"]["ranks_projecting_canonical"]  # 2 front men x 5 reaching ranks = 10
    return {
        "order": order,
        "roman_frontage_m_per_man": sm_rom,
        "macedonians_per_roman_frontage": round(macs, 1),
        "sarissa_points_faced_per_front_roman": int(points),
        "note": "A Roman (open order, ~6 ft) faces ~2 front-rank Macedonians (close order, ~3 ft), each fronting 5 projecting ranks => ~10 sarissa points (Polybius 18.30).",
    }


def feasibility(depth, m):
    warn = []
    reaching = m["sarissa"]["ranks_projecting_canonical"]
    if depth > reaching:
        warn.append(f"Only ~{reaching} of {depth} ranks reach the enemy; the other {depth - reaching} add push/morale, not reach or frontage (L13185).")
    if depth >= 32:
        warn.append("32-deep is the doubled formation: narrower front, more outflankable; useful to limit gaps / resist breakthrough, not to add spear points (L8836).")
    warn.append("Flat, open ground required; flanks/rear and any gap in the line are the decisive weaknesses (L3334,L3632,L3772).")
    return warn


def selftest(m):
    print("selftest: reproducing the book's worked figures")
    ok = True

    v = m["validation"]["syntagma"]
    f = frontage(v["men"], v["ranks"], "close", m)
    pass1 = (f["files"] == v["files"] and v["files"] * v["ranks"] == v["men"])
    print(f"  {'OK ' if pass1 else 'XX '} syntagma: {v['men']} men / {v['ranks']} deep -> {f['files']} files "
          f"(expect {v['files']}; {v['files']}x{v['ranks']}={v['files']*v['ranks']})")
    ok = ok and pass1

    vp = m["validation"]["polybius_projection"]
    p = projection(vp["sarissa_cubits"], vp["grip"], "close", m)
    got = [r["projects_cubits"] for r in p["per_rank"]]
    pass2 = (got == vp["expected_projection_cubits"] and p["ranks_projecting"] == vp["reaching_ranks"])
    print(f"  {'OK ' if pass2 else 'XX '} projection: {vp['sarissa_cubits']}-cubit sarissa -> {got} cubits, "
          f"{p['ranks_projecting']} ranks (expect {vp['expected_projection_cubits']}, {vp['reaching_ranks']})")
    ok = ok and pass2

    vs = m["validation"]["standard_phalanx"]
    f2 = frontage(vs["men"], vs["depth"], vs["order"], m)
    pass3 = (f2["files"] == vs["expected_files"] and f2["frontage_m"] == vs["expected_frontage_m"]
             and f2["depth_m"] == vs["expected_depth_m"])
    print(f"  {'OK ' if pass3 else 'XX '} standard phalanx: {vs['men']} men / {vs['depth']} deep close-order -> "
          f"{f2['files']} files, {f2['frontage_m']} m front, {f2['depth_m']} m deep "
          f"(expect {vs['expected_files']}/{vs['expected_frontage_m']}/{vs['expected_depth_m']})")
    ok = ok and pass3

    print("RESULT:", "PASS — calculator matches the book" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Macedonian phalanx formation advisor (Taylor 2020)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("frontage")
    a.add_argument("--men", type=int, required=True)
    a.add_argument("--depth", type=int, default=16)
    a.add_argument("--order", default="close")

    b = sub.add_parser("line")
    b.add_argument("--length-m", type=float, required=True)
    b.add_argument("--depth", type=int, default=16)
    b.add_argument("--order", default="close")

    c = sub.add_parser("projection")
    c.add_argument("--sarissa-cubits", type=float, default=14)
    c.add_argument("--grip", default="polybius_counterweight",
                   choices=["polybius_counterweight", "rear_grip", "polybius", "rear"])
    c.add_argument("--order", default="close")

    u = sub.add_parser("unit")
    u.add_argument("--men", type=int)
    u.add_argument("--name")
    d = sub.add_parser("density")
    d.add_argument("--order", default="close")
    sub.add_parser("model")
    sub.add_parser("selftest")
    args = ap.parse_args()
    m = load_model()

    if args.cmd == "frontage":
        out = frontage(args.men, args.depth, args.order, m)
        out["feasibility"] = feasibility(args.depth, m)
        print(json.dumps(out, indent=2))
    elif args.cmd == "line":
        print(json.dumps(men_for_line(args.length_m, args.depth, args.order, m), indent=2))
    elif args.cmd == "projection":
        grip = {"polybius": "polybius_counterweight", "rear": "rear_grip"}.get(args.grip, args.grip)
        print(json.dumps(projection(args.sarissa_cubits, grip, args.order, m), indent=2))
    elif args.cmd == "unit":
        if args.name:
            print(json.dumps(lookup_unit(args.name, m), indent=2))
        elif args.men:
            print(json.dumps(decompose_units(args.men, m), indent=2))
        else:
            print("give --men N or --name <unit>", file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "density":
        print(json.dumps(density(args.order, m), indent=2))
    elif args.cmd == "model":
        print(json.dumps(m, indent=2))
    elif args.cmd == "selftest":
        sys.exit(selftest(m))


if __name__ == "__main__":
    main()
