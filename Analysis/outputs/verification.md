# Independent reference check

Checked mapped start counts, vehicle proportions, and street-name joins for GBSIDs 16907, 17120, and 19543. These IDs came from the initial preview, not from selecting extreme analysis results.

Expected counts come from a new grouped query to the city's trip API; expected street names come from a separate street-service query. Neither reference is computed from the local output being checked. The full requests and responses are saved in [verification_reference.json](verification_reference.json).

| GBSID | Authoritative street (from → to) | API scooters | API bicycles | Expected scooter fraction | Output counts | Output scooter share | Match |
|---:|---|---:|---:|---|---|---:|---|
| 16907 | 6TH AVE N (3RD ST N → WASHINGTON AVE N) | 1,480 | 260 | 1480/1740 = 85.0575% | 1480 + 260 = 1740 | 85.0575% | True |
| 17120 | 1ST AVE N (3RD ST N → 4TH ST N) | 654 | 109 | 654/763 = 85.7143% | 654 + 109 = 763 | 85.7143% | True |
| 19543 | 8TH ST N (1ST AVE N → HENNEPIN AVE) | 417 | 76 | 417/493 = 84.5842% | 417 + 76 = 493 | 84.5842% | True |

All comparisons matched.

This verifies three specific counts, proportions, and attribute joins against the published services. It does not verify every segment, the accuracy of the original vendor records, or the geometry's real-world alignment.

For the student: inspect these rows and explain the count/total arithmetic yourself before treating this as your completed Task 7.3 verification.
