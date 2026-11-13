"""Check three mapped segment counts against a separate authoritative API query.

First run: python3 Analysis/verify_spatial.py --fetch-reference
Later runs use the saved reference: python3 Analysis/verify_spatial.py
Reference IDs were chosen from the initial preview, before the spatial results.
"""

import argparse
import csv
import json
import math
from fractions import Fraction
from urllib.parse import urlencode
from urllib.request import urlopen

from Codex_activity import OUTPUT


IDS = (16907, 17120, 19543)
REFERENCE = OUTPUT / "verification_reference.json"
TRIP_QUERY = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/_Motorized_Scooter_and_eBike_Trips_2025/FeatureServer/0/query"
STREET_QUERY = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/PW_Street_Centerline/FeatureServer/0/query"


def get_reference():
    trip_params = {"f": "json", "where": "StartCenterlineType = 'street' AND StartCenterlineID IN (16907,17120,19543)",
                   "groupByFieldsForStatistics": "StartCenterlineID,vehicleType",
                   "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "ObjectId", "outStatisticFieldName": "reference_count"}]),
                   "returnGeometry": "false"}
    street_params = {"f": "json", "where": "GBSID IN (16907,17120,19543)",
                     "outFields": "OBJECTID,GBSID,STREET_O_NAME,STREET_F_NAME,STREET_T_NAME", "returnGeometry": "false"}
    saved = {}
    for name, url, params in (("trips", TRIP_QUERY, trip_params), ("streets", STREET_QUERY, street_params)):
        with urlopen(url, data=urlencode(params).encode(), timeout=90) as response:
            result = json.load(response)
        if "error" in result or result.get("exceededTransferLimit"):
            raise RuntimeError(f"Invalid verification reference: {result}")
        saved[name] = {"url": url, "parameters": params, "response": result}
    REFERENCE.write_text(json.dumps(saved, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-reference", action="store_true")
    args = parser.parse_args()
    if args.fetch_reference:
        get_reference()
    reference = json.loads(REFERENCE.read_text())
    expected = {key: {"scooter": 0, "bicycle": 0} for key in IDS}
    for feature in reference["trips"]["response"]["features"]:
        attrs = feature["attributes"]
        expected[int(attrs["StartCenterlineID"])][attrs["vehicleType"]] = attrs["reference_count"]
    names = {}
    for feature in reference["streets"]["response"]["features"]:
        attrs = feature["attributes"]
        key = attrs["GBSID"]
        if key in names:
            raise ValueError("Verification key is not unique in the source street network")
        names[key] = attrs
    with (OUTPUT / "segment_vehicle_shares.csv").open(newline="") as file:
        observed = {int(row["GBSID"]): row for row in csv.DictReader(file) if int(row["GBSID"]) in IDS}
    lines = ["# Independent reference check", "",
             "Checked mapped start counts, vehicle proportions, and street-name joins for GBSIDs 16907, 17120, and 19543. These IDs came from the initial preview, not from selecting extreme analysis results.",
             "", "Expected counts come from a new grouped query to the city's trip API; expected street names come from a separate street-service query. Neither reference is computed from the local output being checked. The full requests and responses are saved in [verification_reference.json](verification_reference.json).", "",
             "| GBSID | Authoritative street (from → to) | API scooters | API bicycles | Expected scooter fraction | Output counts | Output scooter share | Match |",
             "|---:|---|---:|---:|---|---|---:|---|"]
    comparisons = []
    for key in IDS:
        counts = expected[key]
        n = counts["scooter"] + counts["bicycle"]
        if n == 0:
            raise ValueError(f"No reference trips for {key}")
        expected_share = float(Fraction(counts["scooter"], n))
        row = observed[key]
        attrs = names[key]
        match = (int(row["scooter"]) == counts["scooter"] and int(row["bicycle"]) == counts["bicycle"]
                 and int(row["total_starts"]) == n and math.isclose(float(row["scooter_share"]), expected_share, abs_tol=1e-12)
                 and row["street_name"] == attrs["STREET_O_NAME"]
                 and row["from_street"] == attrs["STREET_F_NAME"] and row["to_street"] == attrs["STREET_T_NAME"])
        comparisons.append(match)
        label = f'{attrs["STREET_O_NAME"]} ({attrs["STREET_F_NAME"]} → {attrs["STREET_T_NAME"]})'
        lines.append(f'| {key} | {label} | {counts["scooter"]:,} | {counts["bicycle"]:,} | {counts["scooter"]}/{n} = {expected_share:.4%} | {row["scooter"]} + {row["bicycle"]} = {row["total_starts"]} | {float(row["scooter_share"]):.4%} | {match} |')
    lines.extend(["", "All comparisons matched." if all(comparisons) else "At least one comparison failed; inspect before interpreting results.",
                  "", "This verifies three specific counts, proportions, and attribute joins against the published services. It does not verify every segment, the accuracy of the original vendor records, or the geometry's real-world alignment.",
                  "", "For the student: inspect these rows and explain the count/total arithmetic yourself before treating this as your completed Task 7.3 verification.", ""])
    (OUTPUT / "verification.md").write_text("\n".join(lines))
    print("\n".join(lines))
    if not all(comparisons):
        raise ValueError("Reference check failed")


if __name__ == "__main__":
    main()
