# Codex Activity

**Sohail Mohammed Khan and Dooley Kim**

Dataset: [Minneapolis Scooter and eBike Trips 2025](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore).

## Task 3.1 — First interaction

- Codex started with Python and the city's API without asking what we wanted to focus on. It did check the units and catch the conflicting 2024/2025 descriptions.
- It clearly labeled the first 1,000 rows as an ordered preview, not a random sample.
- The code had comments but was longer than necessary. Changes to the saved writeup also caused confusion because our editor showed an older version.

## Task 4.1 — Exploration

- Codex summarized all **1,024,014 trips and 11 columns** and made labeled charts. The mean duration was **12.51 minutes**, compared with a median of **7.87 minutes**.
- We'd start with the full CSV and a shorter pandas script next time. The API requests and custom plotting code added complexity.
- Missing locations needed careful handling: **17,551 trail starts** and **17,823 trail ends** lack IDs. These trips can still be included in duration and distance summaries.

Duration and distance are numeric measurements; vehicle and centerline types are categories; start/end times are datetimes. The remaining fields are identifiers. The full dataset is **76.05% scooters** and **23.95% bicycles**, which the source describes as e-bikes.

| Measurement | Mean | Median |
|---|---:|---:|
| Duration (minutes) | 12.51 | 7.87 |
| Distance (kilometers) | 2.31 | 1.56 |

See the [exploration charts and variable summaries](Analysis/outputs/exploration.md) and [exploration code](Analysis/Codex_activity.py).

## Task 5.1 — Mapping

- Codex found the street network and correctly treated centerline IDs as join keys, not coordinates.
- Checking the join was harder than drawing the map. We excluded unmatched IDs and IDs that appeared more than once in the network to avoid assigning trips to uncertain locations.
- Next time, we'd check key uniqueness and match coverage first. Here, **895,767 starts (87.48%)** matched one street feature.

The map excludes **17,551 nonstreet starts**, **95,001 starts with unmatched street IDs**, and **15,695 starts with ambiguous IDs**. These plus the mapped starts account for all trips. It shows start locations, not routes.

![Trip starts by street segment](Analysis/outputs/trip_start_counts_map.svg)

Code: [spatial_analysis.py](Analysis/spatial_analysis.py). Details: [join audit](Analysis/outputs/spatial_audit.json).

## Task 6.1 — Candidate questions

- **How do duration and distance differ between scooters and e-bikes?** Easy to answer with existing fields, but long trips could pull up averages. We'd need medians and the recorded duration because timestamps are rounded.
- **How do scooter and e-bike shares vary across start segments?** Builds on the map and shows local differences. Missing locations and segments with few starts could affect the comparison.

## Task 6.2 — Final question

**How do scooter and e-bike shares of trip starts vary across Minneapolis street segments in the 2025 release, using segments that match one street feature and have at least 100 starts?**

We chose this because it builds on our map and looks at differences between places. The duration question was also feasible, but it made less use of the spatial data.

## Task 7.1 — Plan and decision

- Use the full CSV, check TripID uniqueness, and count scooter and bicycle street starts by start ID. Join only IDs that match one street feature, recording exclusions.
- Keep segments with **at least 100 starts**. Calculate scooter share as scooter starts divided by scooter plus bicycle starts; bicycle share is the remainder.
- Map counts and shares, then summarize the share range and how many segments have a majority of each vehicle type.
- Check selected counts, shares, and street names against separate queries to the city's services.

**Decision:** We chose 100 starts instead of 50 to reduce the influence of small counts. This retains **1,775 segments**, compared with **2,641** at a minimum of 50, but doesn't make every percentage equally reliable.

## Task 7.2 — Results and implementation

The comparison covers **1,775 segments and 760,736 starts**. Scooter shares range from **7.91% to 98.61%**. Scooters have a majority on **1,686 segments**, bicycles on **86**, and **3** are tied. Overall, **77.27%** of these starts are scooters.

One issue was repeated GBSIDs: ID 11022 appeared on two pieces of 21ST AVE S. The revised code excludes all **251 repeated network IDs**, removing **15,695 starts** rather than duplicating counts or guessing a location.

![Scooter share on segments with at least 100 starts](Analysis/outputs/scooter_share_map.svg)

See the [results](Analysis/outputs/spatial_analysis.md) and [segment table](Analysis/outputs/segment_vehicle_shares.csv).

## Task 7.3 — Verification

- **What and why:** Check the counts, scooter share, and street join for GBSID **16907**, since a wrong join or denominator would affect the map.
- **Reference:** A separate city trip-service query returned **1,480 scooter starts and 260 bicycle starts**. The street service identifies this as **6TH AVE N, from 3RD ST N to WASHINGTON AVE N**. These references came from the services, not our local output.
- **Comparison:** The expected share is **1480 / (1480 + 260) × 100 = 85.0575%**. The analysis gives the same counts, share, and street names.
- **Conclusion:** This case needed no further correction after the repeated-key fix. Two additional segments also matched. These checks support the selected records, not every segment or the accuracy of the original trip data.

The [verification report](Analysis/outputs/verification.md), [source queries and responses](Analysis/outputs/verification_reference.json), and [checking code](Analysis/verify_spatial.py) contain the evidence.

## Interpretation and limits

- Duration is in seconds and distance in meters; the tables convert them to minutes and kilometers. Rounded timestamps should not be used to calculate trip duration.
- The title says 2025 but the description mentions 2024. UTC start times actually span April 8, 2025 through January 1, 2026; local dates can differ.
- The current street network may differ from the 2025 network. Missing and excluded locations could change the vehicle mix we see.
- These are recorded start shares, not routes or rider preferences. Availability, pricing, and other possible explanations weren't tested.

## Files and remaining review

See [data/README.md](data/README.md) for downloads and rerun commands. Code, maps, and verification are saved in [our fork](https://github.com/my-name-arch/ds-456-codex-activity).

**Before submission:** Review these draft reflections, inspect the verification counts and arithmetic ourselves, and complete the separate Plan-mode review required by the assignment.
