"""Check four mapped segments and one ambiguous ID against separate API queries.

First run: python3 Analysis/verify_spatial.py --fetch-reference
Later runs use the saved reference: python3 Analysis/verify_spatial.py
The original three IDs came from the preview. The retrospective review adds a
bicycle-heavy segment and the repeated ID that exposed an ambiguous join.
"""

import argparse
import csv
import json
import math
from fractions import Fraction
from urllib.parse import urlencode
from urllib.request import urlopen

from Codex_activity import OUTPUT


IDS = (16907, 17120, 19543, 14327)
AMBIGUOUS_ID = 11022
REFERENCE_IDS = (*IDS, AMBIGUOUS_ID)
REFERENCE = OUTPUT / "verification_reference.json"
TRIP_QUERY = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/_Motorized_Scooter_and_eBike_Trips_2025/FeatureServer/0/query"
STREET_QUERY = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/PW_Street_Centerline/FeatureServer/0/query"


def get_reference():
    id_list = ",".join(str(key) for key in REFERENCE_IDS)
    trip_params = {"f": "json", "where": f"StartCenterlineType = 'street' AND StartCenterlineID IN ({id_list})",
                   "groupByFieldsForStatistics": "StartCenterlineID,vehicleType",
                   "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "ObjectId", "outStatisticFieldName": "reference_count"}]),
                   "returnGeometry": "false"}
    street_params = {"f": "json", "where": f"GBSID IN ({id_list})",
                     "outFields": "OBJECTID,GBSID,STREET_O_NAME,STREET_F_NAME,STREET_T_NAME", "returnGeometry": "false"}
    saved = {}
    for name, url, params in (("trips", TRIP_QUERY, trip_params), ("streets", STREET_QUERY, street_params)):
        with urlopen(url, data=urlencode(params).encode(), timeout=90) as response:
            result = json.load(response)
        if "error" in result or result.get("exceededTransferLimit"):
            raise RuntimeError(f"Invalid verification reference: {result}")
        saved[name] = {"url": url, "parameters": params, "response": result}
    REFERENCE.write_text(json.dumps(saved, indent=2) + "\n")


def check_reference(reference, output_dir=OUTPUT):
    """Return evidence and pass/fail results without modifying source outputs."""
    expected = {key: {"scooter": 0, "bicycle": 0} for key in REFERENCE_IDS}
    seen_groups = set()
    for feature in reference["trips"]["response"]["features"]:
        attrs = feature["attributes"]
        key, vehicle = int(attrs["StartCenterlineID"]), attrs["vehicleType"]
        if key not in expected or vehicle not in expected[key] or (key, vehicle) in seen_groups:
            raise ValueError("Unexpected or duplicated reference count group")
        seen_groups.add((key, vehicle))
        expected[key][vehicle] = attrs["reference_count"]
    if {key for key, _ in seen_groups} != set(REFERENCE_IDS):
        raise ValueError("Reference is missing check IDs; rerun with --fetch-reference")
    names = {}
    for feature in reference["streets"]["response"]["features"]:
        attrs = feature["attributes"]
        key = attrs["GBSID"]
        names.setdefault(key, []).append(attrs)
    for key in IDS:
        if len(names.get(key, [])) != 1:
            raise ValueError(f"Mapped check ID {key} must match exactly one source street feature")
    with (output_dir / "segment_vehicle_shares.csv").open(newline="") as file:
        rows = list(csv.DictReader(file))
    observed = {int(row["GBSID"]): row for row in rows}
    if len(observed) != len(rows):
        raise ValueError("Duplicated GBSIDs in mapped segment output")
    with (output_dir / "unmatched_start_ids.csv").open(newline="") as file:
        exclusions = [row for row in csv.DictReader(file) if int(row["GBSID"]) == AMBIGUOUS_ID]
    lines = ["# Independent reference check", "",
             "The original checks use GBSIDs 16907, 17120, and 19543 from the initial preview. The retrospective review adds 14327 because it has a bicycle majority, and 11022 because its repeated network ID exposed an ambiguous join. These are targeted checks, not a random sample.",
             "", "Expected counts come from a separate grouped query to the city's trip API; street names and feature multiplicity come from the street service. Neither reference is computed from the local output being checked. Both services describe the same published source data, so this checks processing rather than real-world source accuracy. Full requests and responses: [verification_reference.json](verification_reference.json).", "",
             "## Mapped segments", "",
             "| GBSID | Authoritative street (from → to) | API scooters | API bicycles | Expected scooter fraction | Output counts | Output scooter share | Match |",
             "|---:|---|---:|---:|---|---|---:|---|"]
    comparisons = []
    for key in IDS:
        counts = expected[key]
        n = counts["scooter"] + counts["bicycle"]
        if n == 0:
            raise ValueError(f"No reference trips for {key}")
        expected_share = float(Fraction(counts["scooter"], n))
        if key not in observed:
            raise ValueError(f"Mapped check ID {key} is missing from the output")
        row = observed[key]
        attrs = names[key][0]
        match = (int(row["scooter"]) == counts["scooter"] and int(row["bicycle"]) == counts["bicycle"]
                 and int(row["total_starts"]) == n
                 and math.isclose(float(row["scooter_share"]), expected_share, rel_tol=0, abs_tol=1e-12)
                 and math.isclose(float(row["bicycle_share"]), 1 - expected_share, rel_tol=0, abs_tol=1e-12)
                 and row["street_name"] == attrs["STREET_O_NAME"]
                 and row["from_street"] == attrs["STREET_F_NAME"] and row["to_street"] == attrs["STREET_T_NAME"])
        comparisons.append(match)
        label = f'{attrs["STREET_O_NAME"]} ({attrs["STREET_F_NAME"]} → {attrs["STREET_T_NAME"]})'
        lines.append(f'| {key} | {label} | {counts["scooter"]:,} | {counts["bicycle"]:,} | {counts["scooter"]}/{n} = {expected_share:.4%} | {row["scooter"]} + {row["bicycle"]} = {row["total_starts"]} | {float(row["scooter_share"]):.4%} | {match} |')
    attrs = names.get(AMBIGUOUS_ID, [])
    counts = expected[AMBIGUOUS_ID]
    n = counts["scooter"] + counts["bicycle"]
    repeated = len(attrs) > 1 and len({row["OBJECTID"] for row in attrs}) == len(attrs)
    absent = AMBIGUOUS_ID not in observed
    exclusion = exclusions[0] if len(exclusions) == 1 else None
    exclusion_matches = (exclusion is not None and n > 0
                         and exclusion["exclusion_reason"] == "ambiguous_network_id"
                         and int(exclusion["scooter"]) == counts["scooter"]
                         and int(exclusion["bicycle"]) == counts["bicycle"]
                         and int(exclusion["total_starts"]) == n)
    comparisons.append(repeated and absent and exclusion_matches)
    lines.extend(["", f"## Ambiguous ID {AMBIGUOUS_ID}", "",
                  f"- Source street features: **{len(attrs)}**; repeated ID confirmed: **{repeated}**."])
    for attrs_row in attrs:
        lines.append(f'- OBJECTID {attrs_row["OBJECTID"]}: {attrs_row["STREET_O_NAME"]}, {attrs_row["STREET_F_NAME"]} → {attrs_row["STREET_T_NAME"]}.')
    output_counts = "missing or duplicated exclusion row" if exclusion is None else f'{exclusion["scooter"]} scooter + {exclusion["bicycle"]} bicycle = {exclusion["total_starts"]}; reason: {exclusion["exclusion_reason"]}'
    lines.extend([f"- API trip counts: **{counts['scooter']} scooter + {counts['bicycle']} bicycle = {n}**.",
                  f"- Absent from mapped segment table: **{absent}**.",
                  f"- Exclusion output: {output_counts}; matches reference and expected reason: **{exclusion_matches}**.",
                  "", "All five checks passed." if all(comparisons) else "At least one check failed; inspect before interpreting results.",
                  "", "These checks cover four mapped segments and one ambiguous-ID exclusion. They do not verify every segment, the accuracy of the original vendor records, or the geometry's real-world alignment.",
                  "", "For the student: inspect these rows and explain the count/total arithmetic yourself before treating this as your completed Task 7.3 verification.", ""])
    return lines, comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-reference", action="store_true")
    args = parser.parse_args()
    if args.fetch_reference:
        get_reference()
    reference = json.loads(REFERENCE.read_text())
    lines, comparisons = check_reference(reference)
    (OUTPUT / "verification.md").write_text("\n".join(lines))
    print("\n".join(lines))
    if not all(comparisons):
        raise ValueError("Reference check failed")


if __name__ == "__main__":
    main()
