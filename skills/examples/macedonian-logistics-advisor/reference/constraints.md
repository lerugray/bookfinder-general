# Logistics as the Binding Constraint — Engels's Macedonian Supply Model

Source: Donald W. Engels, *Alexander the Great and the Logistics of the Macedonian Army* (1978). Line citations refer to `content.md` in this directory. Thesis: logistics, not strategy or tactics, set the hard outer limits on where the army could go, how fast, how big, and when. Everything below is a rule a movement/supply system has to obey, not a flavor note.

## Base ration constants (the inputs every rule below depends on)

These are the per-day consumption rates the whole model runs on. Treat them as the unit costs of being alive on the march.

- **Man:** 3 lb grain/day, 2 qt water/day minimum (lines 1991, 1993). The food ration can be cut for short stretches; **the 2-qt water floor cannot** be cut for untrained troops in desert (lines 197, 201).
- **Horse/mule (cavalry + pack):** 10 lb grain + 10 lb forage (straw/chaff) + 8 gal water/day (line 1993). Water swings 5–15 gal with temperature; 8 is the working average (line 220).
- **Camel:** 10 gal water/day, but 20 gal at once after 3–4 dry days (lines 1995, 253).
- **Carry capacity:** a pack animal carries 250 lb but is *itself* eating 20 lb/day of what it carries (grain + forage) (lines 2000, 2079). A man can hump 80 lb total for extended distances, of which ~30 lb can be supplies (lines 1983, 2021, 4016).
- **March rate:** ~15 mpd sustained, ~13 mpd over long distances with halts, 19.5 mpd absolute ceiling (and only achievable when the fleet carried the supplies) (lines 1962, 2007, 7222). **One day's halt in seven is mandatory** — animals can't bear loads 7 consecutive days and need daylight grazing time (line 2115).

---

## 1. The self-carry limit: ~10 days of grain, and it bounds operational range from a depot

**The limit is roughly a 10-day grain ration carried, because a pack animal eats its own cargo and the column needed to carry more becomes physically impossible.**

Mechanism: each pack animal consumes 20 lb/day of its 250-lb load, so the marginal animal added to carry more days of food also adds its own multi-day appetite. The required herd doesn't grow linearly — it explodes. To carry the Hellespont army (~65,000 personnel, 6,100 cavalry horses) you need 1,121 animals for a **1-day** grain supply, 2,840 for 2 days (lines 2000), then **40,350 for 15 days and 107,600 for 20 days** (line 2003). At 25 days the animals have eaten 100% of the load and carry nothing for the men (line 2003).

Why 10 and not 25: the upper end is a fantasy. 107,600 animals in single file stretch 306 miles; even 10-abreast they stretch 31 miles — longer than a day's march, so the tail never catches the head (lines 2005–2007). Engels caps the *real* fleet at ≤20,000 pack animals anywhere on the route (line 2007). With men also carrying 30 lb each, the absolute overland ceiling is a **14-day grain ration, "no matter how many pack animals were with the army"** (lines 2103, 3992).

**Designer rule:** operational radius from a supplied base/depot = (carried days ÷ 2) × march rate, because the force must be able to *return* or reach the next depot before the carried ration zeroes out. A 10-day self-carry buys ~5 marching days out (~75 mi) before resupply is mandatory. This is why the itinerary is a chain of 2–4 day hops between revictualing points (lines 2107–2113), never a long open-country dash.

---

## 2. Water is the *binding* constraint in arid terrain, and it behaves differently from food

**In a desert the limit is water, not food, because the water ration has a hard floor food doesn't have, and water is ~10× heavier than grain per day of supply.**

Two asymmetries make water the killer:

1. **Floor, not slope.** Food can be half-rationed for a stretch; the 2-qt/day water minimum cannot be reduced for untrained troops marching 8 hrs under desert sun (lines 197, 201). You can starve a little; you cannot dehydrate a little.
2. **Mass.** Water weighs 10 lb/gal (line 2015). A man's daily grain is 3 lb; his minimum water is ~5 lb; an animal's daily water (8 gal) is 80 lb — **8× the weight of its 10-lb grain ration.** Carrying water collapses an animal's net payload from 240 lb (grain-only terrain) to **150 lb** (full desert, line 2015).

The full-desert math: where grain, fodder, *and* water all must be carried, you need **8,400 animals for a single day's supply** (line 2015), and it becomes **impossible to carry more than a ~12½-day theoretical / 4-day practical supply at all** — the animals eat through everything by day 4–5 even at half rations (lines 2018, 2034). Engels's hard law: **an animal-and-man-borne column cannot cross terrain with no grain/fodder/water for more than 4 days; on full rations, not more than 2 days without heavy casualties** (line 2034). Empirically confirmed at Siwah — an 8-day grain load but water-for-men-only ran out at day 4, exactly as predicted (lines 2624–2626); Engels found *no* caravan account exceeding 4 waterless days (line 2626).

**Designer rule:** in arid hexes, track water as a separate, heavier resource with a non-reducible per-unit cost and a hard 4-day uncrossable-gap limit. Springs/wells within a 3-day march of each other are what make a desert route legal at all (line 2620). The Siwah-to-Memphis direct line is impassable *because* of a single 120-mile waterless interval (line 2620).

---

## 3. Pack animals beat ox-carts, and the supply column defeats itself

**Carts are out because they're too slow, too fragile, and need special routes; the deeper limit is that overland supply convoys consume their own cargo and so cannot extend the supply line.**

Carts rejected (lines 1960–1969): oxen do 2 mph and work only 5 hrs/day vs 8 for horse/mule, so carts can't hold the ~15-mpd march rate; antiquity's throat-and-girth harness choked the animal the harder it pulled, gutting draft capacity; carts break down, need lumber/spare parts (absent in treeless Iran/Afghanistan), and can't take the same paths as pack animals. Hence Macedonians carried supplies on the *troops* + a minimal pack train, only horses/mules/camels (faster, more endurance than oxen/donkeys) (lines 1971, 2047).

The self-defeating convoy (the load-bearing point): a pack animal hauling grain 5 days out **eats 100 lb of its 200-lb load on the round trip** — delivering exactly enough to pay for its own travel, net zero to the army (line 4952). To resupply the army for 10 days from a 75-mile (5-day) radius would need **28,000+ pack animals that would devour as much food as the entire army combined** (line 4952). This is why overland supply has a hard reach.

**Designer rule:** overland resupply from a depot is only economic inside a **60–80 mile radius** (lines 3420, 4952); beyond that the convoy eats more than it delivers and the line goes net-negative. Sea/river transport sidesteps this entirely (next rule). Carts give a movement-rate and terrain penalty with no compensating range gain — model the Macedonian pack-only doctrine as a speed/mobility buff, not a capacity buff.

---

## 4. Sea, depots, and requisition do the work the pack train can't

**The army can't be self-sufficient more than a few days from a navigable river or seaport, because water transport is the only thing that beats the convoy-eats-its-cargo limit — so the campaign is tethered to the fleet, pre-positioned magazines, and local surrender.**

The transport gap is enormous: a merchant ship carries **400 tons; a pack animal carries 200 lb and burns 20 lb/day moving it** (line 2079). So:

- **Fleet/coastal supply.** Where a coast or river runs alongside the route, the fleet carries the grain, water, and forage and the army marches light (lines 2079, 2105, 2552, 2639). The 19.5-mpd record march (Sinai) happened *only because* the fleet carried supplies (line 7222). Conversely, when the fleet *couldn't* provision (Gedrosia, adverse winds), Alexander was free to leave the coast — and the army nearly died inland (lines 478, 494).
- **Pre-positioned magazines/depots.** Across waterless gaps the army cannot bridge by self-carry, depots of food and water must be built *in advance* along the intended line of march (line 2286); water depots by damming streams or hauling water in (line 2288). Without them, "first the pack animals and then the followers and men would die, desert, or refuse to march" (line 2290).
- **Local requisition + surrender as a logistics act.** Because magazines depend on locals stocking and guarding them, Alexander first secured alliances; not surrendering before he arrived was treated as hostile (lines 2290, 2301). In hard terrain he took hostages or planted garrisons to *guarantee* the depots were filled (lines 2293, 3412). Supplies came by gift, requisition, purchase at markets — or, in un-surrendered country, by pillage/forage (lines 2299, 3414).

**Designer rule:** a navigable-water adjacency is a force-multiplier flag — it removes the carried-days cap and the 60–80 mile depot radius along that edge. Depots are pre-placed supply caches whose existence depends on a diplomatic/control state of the territory; flip that state and the cache vanishes, stranding the column. Bases, winter quarters, and even short halts must sit on water transport (lines 2590–2594, 3420).

---

## 5. Seasonality: the harvest clock gates the whole campaign

**The march start and direction are pinned to harvest dates, because subsistence farmers have no surplus to requisition in the pre-harvest "hunger gap."**

Mechanism: ancient agriculture ran at subsistence; in the weeks before harvest farmers' own caloric intake drops below maintenance and they have *nothing* to give an army even under compulsion (lines 2096–2098). So an army can't live off the land out of season at any price. Alexander therefore:

- **Carried a 30-day grain load out of the home base** specifically to bridge from a late-March/April start to the May–June harvest (lines 2088, 2098). The 30 days "synchronizes the march with the harvest date" — run out exactly when the standing crop becomes edible (lines 2098, 2100).
- **Wintered in place** until winter wheat/barley were harvested before marching (line 3418); timed crossings of mountains to when valley harvests (July–Aug) made foraging possible, or carried over the gap when they didn't (lines 3227, 3074).
- **Timed against the enemy's clock too:** the early start (bought by the 30-day load) let him beat the Persian fleet, which couldn't be provisioned before June (line 2166).

**Designer rule:** terrain yields *forage/requisition supply only in season*; out of season a region's supply value drops to near zero regardless of its normal richness. Campaign start dates carry a hidden ration cost = (days until local harvest) × consumption, which must be carried or shipped. The harvest date is a per-region calendar variable, and the optimal move is to arrive as the crop ripens.

---

## 6. Army size ↔ route ↔ survivability are one coupled equation

**A bigger army is not simply stronger — past a threshold it is *less* survivable on a constrained route, because consumption and column length scale with size while route capacity (water points, forage radius, pass width) does not.**

Three coupled mechanisms:

1. **Consumption vs. local supply.** A region's surplus within the 60–80 mile radius is fixed; the larger the force, the faster it strips that surplus and the sooner it must move on (lines 2081, 3420). So large armies *cannot sit still* away from water transport.
2. **Column length vs. route width.** Size determines how long the marching column is, and at a chokepoint (pass, bridge) the **narrowest point sets the crossing rate** — "like water in a funnel" (line 3069). The Hindu Kush crossing took 16–17 days instead of the usual 4 purely because of army size funneling through a 3-abreast pass (lines 3056, 3067). Engels even *back-calculates troop numbers from crossing time* — that's how tight the size↔time coupling is (lines 3063–3069).
3. **The survivability kill.** When a long column crosses devastated terrain, the *lead* elements carry their 10-day ration but then **wait ~2 weeks in stripped country for the tail to clear the pass** — and starve while waiting (line 3074). Larger army → longer column → longer wait → the carried ration is consumed *before the army is even reassembled.* Size converts directly into starvation risk on a narrow, barren route.

**Countermeasures Alexander used (the designer's levers):**
- **Divide the army** into smaller units in hard-supply terrain so each unit's smaller requirement fits the local radius (lines 2225, 2592, 3414, 3422). Standard procedure before Persis, the Dasht-i-Kavir, Sogdia, Gedrosia (line 4381).
- **Advance with a small light force** while the main army stays at a supplied base, when entering un-surrendered country (line 3414).
- **Never commit the whole army into un-surrendered, un-scouted territory** — intelligence on routes/climate/resources comes first (line 3414).
- **Route through populous, cultivated land**, never open uninhabited country, because supply only exists near settlement (line 3422).

**Designer rule:** make supply consumption and column length both scale with stack size, while route attributes (water-point capacity, forage radius, chokepoint throughput) are fixed properties of the hex/edge. This makes "split the stack" a real, rewarded decision in arid/mountainous terrain, and makes large stacks a liability — not an asset — on a barren narrow route. The lead-element-starves-waiting-for-the-tail effect is the mechanism that should punish marching an oversized army through a single chokepoint into devastated land.

---

## One-line summary of the model

The army can self-carry ~10 days of grain (14 absolute) and survive at most 4 days with no water/food/forage at all, because pack animals eat their own cargo; overland resupply is economic only within 60–80 miles of a depot for the same reason; so the campaign is structurally tethered to the fleet, pre-positioned magazines, and in-season local requisition secured by surrender — and it is gated by the harvest clock and by an army-size/route-capacity coupling that makes large forces *less* survivable on arid, narrow routes. Logistics, not the enemy, drew the map of where Alexander could go.
