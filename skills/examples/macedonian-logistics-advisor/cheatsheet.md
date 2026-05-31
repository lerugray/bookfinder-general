# Macedonian Logistics — Cheatsheet (Engels 1978)

Quick-reference rating tables. For computation use `scripts/advise.py`; every number here is in `data/rates.json` with line citations.

## Daily consumption (per individual)
| Entity | Grain | Water | Forage |
|---|---|---|---|
| Soldier / follower | 3 lb | 2 qt (0.5 gal) | — |
| Cavalry / pack horse / mule | 10 lb | 8 gal | 10 lb |
| Camel | 10 lb | 10 gal | 25 lb straw |
| Elephant | 500 lb | 60 gal | — |
| Ox team (2, **banned**) | 100 lb | — | — |

Water floor: **2 qt/man/day cannot be cut** in desert. Water weighs **10 lb/Imp gal**.

## Carrying capacity
| Carrier | Carries | Note |
|---|---|---|
| Soldier | 80 lb total (~30 lb food) | self-carries panoply + rations |
| Pack horse/mule | 200 lb | |
| Camel | 300 lb | water-endurance overstated |
| Avg pack animal (model) | **250 lb**, eats 20 lb/day of it | the unit `advise.py` uses |
| 2-ox cart | 1,000–1,200 lb pull | too slow (2 mph) — banned |

## March rates (miles/day)
| Condition | mpd |
|---|---|
| Long-haul average (with rest days) | **13** |
| Planning rate (1 halt in 7) | **15** |
| Whole-army maximum (fleet-fed, Sinai) | 19.5 |
| Small detached light unit | 40–50 |
| Infantry on the move | 2.5–3 mph (not a daily rate) |

**Mandatory: 1 rest day every 5–7 marching days** → 15 mpd nets to ~13 mpd.

## Operational limits (the hard walls)
| Limit | Value | Why |
|---|---|---|
| Self-carry **grain only** (water+forage local) | ~10 days practical (25 theoretical) | animal eats 10 lb grain/day of its load |
| Self-carry **grain + forage** (water local) | ~7 days practical (12.5 theoretical) | eats 20 lb/day |
| **Full desert** (nothing available) | **4 days** half-ration / 2 days full | the book's central result |
| Max waterless interval | ~4 days ≈ 120 mi | no caravan exceeds it |
| Economic resupply radius from depot | **60–80 mi** | beyond it the convoy eats more than it delivers |
| Absolute overland grain ceiling | 14 days | "no matter how many pack animals" |
| Realistic pack-animal fleet | ≤ 20,000 | more = column longer than a day's march |

**The 1:10 law:** an animal's daily feed ≈ 1/10 of what it can carry, *regardless of animal size* — this fixed ratio is what makes the desert range a hard physical wall.

## Designer's one-liner
Self-carry ~10 days of grain (14 absolute), survive at most 4 days with nothing available, resupply only within 60–80 mi of a depot — because **pack animals eat their own cargo**. So the campaign is tethered to fleet + magazines + in-season requisition, gated by the harvest clock, and *bigger armies are less survivable* on arid, narrow routes (consumption + column length scale; water points + pass width don't).
