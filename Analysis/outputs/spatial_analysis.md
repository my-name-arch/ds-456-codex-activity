# Street-segment vehicle comparison

Research question: How do scooter and e-bike proportions vary across street segments where trips start, among matched segments with at least 100 recorded starts?

- Full CSV: 1,024,014 trips; 1,024,014 distinct TripIDs.
- Street network: 13,021 features; 251 non-null GBSIDs repeat and are excluded from the join; 527 features lack a GBSID.
- Matched: 895,767 trip starts on 9,194 segments (87.48% of all trips).
- Excluded starts: {'nonstreet_start': 17551, 'unmatched_street_id': 95001, 'ambiguous_network_id': 15695}; unmatched distinct street IDs: 1,166; ambiguous distinct trip-start IDs: 150.
- Comparison subset: 1,775 segments with at least 100 starts, containing 760,736 starts.
- Pooled scooter share in this subset: 77.27%; median segment scooter share (equal weight per segment): 76.89%.
- Segment scooter shares range from 7.91% to 98.61%.
- Scooter-majority segments: 1,686; bicycle-majority: 86; ties: 3.

![Scooter share map](scooter_share_map.svg)

![Trip start counts map](trip_start_counts_map.svg)

## Examples: five lowest and five highest scooter shares

| GBSID | Street | From | To | Scooter | Bicycle | Total | Scooter share |
|---:|---|---|---|---:|---:|---:|---:|
| 14327 | 3RD AVE S | 46TH ST E | 45TH ST E | 11 | 128 | 139 | 7.91% |
| 16366 | LOGAN AVE N | 26TH AVE N | 27TH AVE N | 16 | 135 | 151 | 10.60% |
| 14314 | 5TH AVE S | 43RD ST E | 42ND ST E | 21 | 92 | 113 | 18.58% |
| 13180 | STINSON BLVD | 32ND AVE NE | 33RD AVE NE | 28 | 120 | 148 | 18.92% |
| 16985 | FRANKLIN AVE E | CEDAR AVE S | MINNEHAHA AVE | 47 | 193 | 240 | 19.58% |
| 16417 | PARK AVE | LAKE ST E | 28TH ST E | 106 | 4 | 110 | 96.36% |
| 11622 | LONGFELLOW AVE | 34TH ST E | 33RD ST E | 99 | 3 | 102 | 97.06% |
| 14597 | THOMAS AVE N | GOLDEN VALLEY RD | 21ST AVE N | 184 | 5 | 189 | 97.35% |
| 17057 | PILLSBURY AVE | 26TH ST W | 25TH ST W | 203 | 5 | 208 | 97.60% |
| 16922 | CLEVELAND ST NE | BROADWAY ST NE | DEAD END (N) | 142 | 2 | 144 | 98.61% |

## Minimum-start comparison

All cutoffs use the same uniquely matched street segments. The main maps and results retain the 100-start minimum.

| Minimum starts | Segments | Trip starts | Overall scooter share |
|---:|---:|---:|---:|
| 50 | 2,641 | 822,091 | 76.82% |
| 100 | 1,775 | 760,736 | 77.27% |
| 200 | 1,033 | 655,339 | 78.02% |

The overall scooter share changes little across these cutoffs. The included segments and their individual percentages can still differ. The cutoff does not guarantee statistical reliability. Full values: [threshold_comparison.csv](threshold_comparison.csv).

## Interpretation limits

The unit is a recorded trip start, not a rider or a route. The 100-start threshold reduces the influence of very small denominators; it is a descriptive choice, not a statistical significance test. Segment-level summaries weight each eligible segment equally; pooled shares weight by trip count. No causal explanation or rider preference can be inferred. Shared-vehicle availability, pricing, land use, and program coverage were not controlled. Current street geometry may differ from the network used in 2025; unmatched and ambiguous IDs are listed rather than guessed. GBSIDs attached to multiple network features are excluded to avoid multiplying trip counts or assigning starts to an uncertain geometry.

Sources: [trip table](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore), [PW Street Centerline](https://opendata.minneapolismn.gov/datasets/pw-street-centerline/about).
