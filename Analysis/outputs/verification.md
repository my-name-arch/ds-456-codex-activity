# Independent reference check

The original checks use GBSIDs 16907, 17120, and 19543 from the initial preview. The retrospective review adds 14327 because it has a bicycle majority, and 11022 because its repeated network ID exposed an ambiguous join. These are targeted checks, not a random sample.

Expected counts come from a separate grouped query to the city's trip API; street names and feature multiplicity come from the street service. Neither reference is computed from the local output being checked. Both services describe the same published source data, so this checks processing rather than real-world source accuracy. Full requests and responses: [verification_reference.json](verification_reference.json).

## Mapped segments

| GBSID | Authoritative street (from → to) | API scooters | API bicycles | Expected scooter fraction | Output counts | Output scooter share | Match |
|---:|---|---:|---:|---|---|---:|---|
| 16907 | 6TH AVE N (3RD ST N → WASHINGTON AVE N) | 1,480 | 260 | 1480/1740 = 85.0575% | 1480 + 260 = 1740 | 85.0575% | True |
| 17120 | 1ST AVE N (3RD ST N → 4TH ST N) | 654 | 109 | 654/763 = 85.7143% | 654 + 109 = 763 | 85.7143% | True |
| 19543 | 8TH ST N (1ST AVE N → HENNEPIN AVE) | 417 | 76 | 417/493 = 84.5842% | 417 + 76 = 493 | 84.5842% | True |
| 14327 | 3RD AVE S (46TH ST E → 45TH ST E) | 11 | 128 | 11/139 = 7.9137% | 11 + 128 = 139 | 7.9137% | True |

## Ambiguous ID 11022

- Source street features: **2**; repeated ID confirmed: **True**.
- OBJECTID 484: 21ST AVE S, 31ST ST E → 30 1/2 ST E.
- OBJECTID 557: 21ST AVE S, 30 1/2 ST E → LAKE ST E.
- API trip counts: **96 scooter + 24 bicycle = 120**.
- Absent from mapped segment table: **True**.
- Exclusion output: 96 scooter + 24 bicycle = 120; reason: ambiguous_network_id; matches reference and expected reason: **True**.

All five checks passed.

These checks cover four mapped segments and one ambiguous-ID exclusion. They do not verify every segment, the accuracy of the original vendor records, or the geometry's real-world alignment.

For the student: inspect these rows and explain the count/total arithmetic yourself before treating this as your completed Task 7.3 verification.
