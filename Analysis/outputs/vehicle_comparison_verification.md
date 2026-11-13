# Vehicle-comparison verification

Expected results were recalculated directly from the full raw CSV, using `statistics.median` and `statistics.quantiles(method='inclusive')`. This does not reuse the analysis frequency-counter percentile calculation or derive expectations from the saved summary. It verifies processing of the same source, not the accuracy of vendor records.

Raw rows: **1,024,014**; unique nonmissing TripIDs confirmed; unexpected vehicle categories: `{}`. Vehicle counts and each measurement's valid/excluded counts reconcile.

## Full-data comparison

All four vehicle/measurement groups match: total trips, valid n, five exclusion counts, units, and all three quantiles. Numeric tolerance is absolute **1e-9**, using unrounded table values.

| Vehicle | Unit | Valid n | Expected q25 | Expected median | Expected q75 | Result |
|---|---|---:|---:|---:|---:|---|
| scooter | minutes | 778,738 | 4.400000000 | 7.466666667 | 13.683333333 | PASS |
| scooter | kilometers | 778,738 | 0.808000000 | 1.479000000 | 2.650000000 | PASS |
| bicycle | minutes | 245,276 | 5.316666667 | 9.283333333 | 17.000000000 | PASS |
| bicycle | kilometers | 245,276 | 0.955000000 | 1.859000000 | 3.499000000 | PASS |

## Source-record unit checks

These are the first five source records per vehicle ordered by ObjectId, not a random sample. Raw seconds / 60 = minutes; raw meters / 1000 = kilometers. Invalid measurements would be marked excluded.

| Vehicle | ObjectId | TripID | Raw seconds | Minutes | Raw meters | Kilometers |
|---|---:|---:|---:|---:|---:|---:|
| scooter | 1 | 107916 | 230 | 3.833333333 | 924 | 0.924000000 |
| scooter | 2 | 107919 | 4216 | 70.266666667 | 13485 | 13.485000000 |
| scooter | 3 | 107917 | 361 | 6.016666667 | 901 | 0.901000000 |
| scooter | 4 | 107918 | 3831 | 63.850000000 | 12652 | 12.652000000 |
| scooter | 5 | 107920 | 2023 | 33.716666667 | 6579 | 6.579000000 |
| bicycle | 24 | 1031 | 371 | 6.183333333 | 1573 | 1.573000000 |
| bicycle | 34 | 1250 | 3035 | 50.583333333 | 6614 | 6.614000000 |
| bicycle | 35 | 1277 | 3024 | 50.400000000 | 6958 | 6.958000000 |
| bicycle | 45 | 1275 | 3052 | 50.866666667 | 6941 | 6.941000000 |
| bicycle | 51 | 1143 | 460 | 7.666666667 | 870 | 0.870000000 |

## Error-detection checks

PASS: invalid values, independent measurement filters, unknown categories, inclusive quartiles, single-value and empty groups, missing/duplicate IDs, missing fields, and deliberately altered summaries/counts.

PASS: changing the saved scooter-duration median by 1 minute was rejected.

All checks passed. The source records support checking unit conversions; they do not establish the full-data medians. The separate full-data recalculation above checks those medians and quartiles.

Inspect the source-record conversions and full-data comparison yourself when writing your personal verification reflection. This report does not establish that you have done that review.
