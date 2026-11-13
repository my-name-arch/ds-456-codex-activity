"""Map trip starts and compare recorded vehicle shares by street segment.

Run: python3 Analysis/spatial_analysis.py --download-network  # first run, online
Then: python3 Analysis/spatial_analysis.py                     # cached, offline

Uses the full trip CSV and the official PW Street Centerline GBSID join key.
Outputs are descriptive trip counts, not route use or population preferences.
"""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from decimal import Decimal, InvalidOperation
from html import escape
from statistics import median

from Codex_activity import DATA, FULL_CSV, OUTPUT, fetch


STREET_URL = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/PW_Street_Centerline/FeatureServer/0"
NETWORK = DATA / "streets_26915.json"
MIN_STARTS = 100
COMPARISON_MINIMUMS = (50, 100, 200)
VEHICLES = ("scooter", "bicycle")


def segment_id(value):
    """Normalize integral IDs without rounding or silently truncating a key."""
    if value is None or str(value).strip() == "":
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"Invalid segment ID: {value!r}") from error
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(f"Non-integral segment ID: {value!r}")
    return int(number)


def download_network():
    """Download every feature in stable object-ID order, projected in meters."""
    meta = fetch("street_layer", STREET_URL, {}, False)
    count = fetch("street_count", STREET_URL + "/query",
                  {"where": "1=1", "returnCountOnly": "true"}, False)["count"]
    features = []
    for offset in range(0, count, meta["maxRecordCount"]):
        page = fetch(f"street_page_{offset}", STREET_URL + "/query", {
            "where": "1=1", "outFields": "OBJECTID,GBSID,STREET_O_NAME,STREET_F_NAME,STREET_T_NAME",
            "outSR": 26915, "returnGeometry": "true", "orderByFields": "OBJECTID ASC",
            "resultOffset": offset, "resultRecordCount": meta["maxRecordCount"],
        }, False)
        if page.get("spatialReference", {}).get("wkid") != 26915:
            raise ValueError("Network response was not projected to EPSG:26915")
        features.extend(page["features"])
    if len(features) != count or len({f["attributes"]["OBJECTID"] for f in features}) != count:
        raise ValueError("Incomplete or duplicated paginated network download")
    NETWORK.write_text(json.dumps({"spatialReference": {"wkid": 26915}, "features": features}))


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def compare_minimums(rows):
    """Compare cutoffs on the same uniquely matched segments; do not change maps."""
    comparison = []
    for minimum in COMPARISON_MINIMUMS:
        subset = [row for row in rows if row["total_starts"] >= minimum]
        starts = sum(row["total_starts"] for row in subset)
        comparison.append({
            "minimum_starts": minimum,
            "segments": len(subset),
            "trip_starts": starts,
            "scooter_share": sum(row["scooter"] for row in subset) / starts if starts else None,
        })
    return comparison


def make_map(features, rows, mode, filename):
    """Render projected centerlines with a common extent, legend, north, and scale."""
    lookup = {row["GBSID"]: row for row in rows}
    points = [point for feature in features for path in feature["geometry"]["paths"] for point in path]
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = min(650 / (xmax - xmin), 880 / (ymax - ymin))
    xoffset = 35 + (650 - scale * (xmax - xmin)) / 2
    yoffset = 105 + (880 - scale * (ymax - ymin)) / 2
    if mode == "share":
        title = "Scooter share of recorded street trip starts"
        colors = ["#2166ac", "#67a9cf", "#f7f7b9", "#ef8a62", "#b2182b"]
        labels = ["0 to <20%", "20 to <40%", "40 to <60%", "60 to <80%", "80 to 100%"]
        def color(row):
            return colors[min(4, int(row["scooter_share"] * 5))]
    else:
        title = "Recorded scooter and e-bike starts by street segment"
        colors = ["#c6dbef", "#6baed6", "#3182bd", "#08519c", "#08306b"]
        labels = ["1 to 9", "10 to 99", "100 to 999", "1,000 to 9,999", "10,000+"]
        def color(row):
            return colors[min(4, int(math.log10(row["total_starts"])))]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="1080" viewBox="0 0 1050 1080">',
             f'<title>{escape(title)}</title>', '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" fill="#172b4d">',
             f'<text x="30" y="35" font-size="23">{escape(title)}</text>',
             '<text x="30" y="62" font-size="14">Minneapolis program trips, 2025 release; start locations only</text>',
             '<text x="30" y="85" font-size="13">Street network: current PW Street Centerline; EPSG:26915 (meters)</text>']
    # Paint the base first so low-use segments cannot obscure the colored overlay.
    paths = []
    for feature in features:
        gbsid = segment_id(feature["attributes"]["GBSID"])
        for path in feature["geometry"]["paths"]:
            points_text = " ".join(f'{xoffset + (p[0]-xmin)*scale:.2f},{yoffset + (ymax-p[1])*scale:.2f}' for p in path)
            paths.append((gbsid, points_text))
            parts.append(f'<polyline points="{points_text}" fill="none" stroke="#d9dfe4" stroke-width="0.55"/>')
    for gbsid, points_text in paths:
        row = lookup.get(gbsid)
        if row is None or row["total_starts"] == 0 or (mode == "share" and row["total_starts"] < MIN_STARTS):
            continue
        tooltip = f'GBSID {gbsid}: {row["street_name"]}; {row["total_starts"]:,} starts; scooter share {row["scooter_share"]:.1%}'
        parts.append(f'<polyline points="{points_text}" fill="none" stroke="{color(row)}" stroke-width="1.8"><title>{escape(tooltip)}</title></polyline>')
    parts.append('<text x="725" y="140" font-size="17">Scooter share</text>' if mode == "share" else '<text x="725" y="140" font-size="17">Trip starts</text>')
    for i, (shade, label) in enumerate(zip(colors, labels)):
        y = 165 + 35 * i
        parts.extend([f'<rect x="725" y="{y}" width="27" height="16" fill="{shade}" stroke="#888"/>',
                      f'<text x="765" y="{y+13}" font-size="14">{escape(label)}</text>'])
    threshold = f"Gray: below {MIN_STARTS} starts or excluded" if mode == "share" else "Gray: no matched recorded starts"
    notes = [threshold, "Trail starts excluded (missing IDs).", "Unmatched/ambiguous IDs excluded.", "Each line represents a start segment,", "not the full trip route.", "Scooter + e-bike shares = 100%."]
    for i, note in enumerate(notes):
        parts.append(f'<text x="725" y="{385+i*25}" font-size="13">{escape(note)}</text>')
    parts.extend(['<path d="M 920 625 L 920 565 M 912 578 L 920 565 L 928 578" fill="none" stroke="#172b4d" stroke-width="2"/>',
                  '<text x="914" y="552" font-size="18">N</text>',
                  f'<path d="M 50 1010 h {2000*scale:.2f}" stroke="#172b4d" stroke-width="4"/>',
                  '<text x="50" y="1033" font-size="13">2 km (projected distance)</text>',
                  '<text x="30" y="1060" font-size="12">Sources: City of Minneapolis 2025 trip release and PW Street Centerline. Shares describe observed trips.</text>',
                  '</g></svg>'])
    (OUTPUT / filename).write_text("\n".join(parts))


def analyze():
    if not NETWORK.exists():
        raise FileNotFoundError("Run with --download-network once to cache official street geometry")
    network = json.loads(NETWORK.read_text())
    if network["spatialReference"]["wkid"] != 26915:
        raise ValueError("Expected EPSG:26915 network geometry")
    features = network["features"]
    key_counts = Counter(segment_id(f["attributes"]["GBSID"]) for f in features)
    ambiguous_keys = {key for key, n in key_counts.items() if key is not None and n > 1}
    geometries = {}
    for feature in features:
        key = segment_id(feature["attributes"]["GBSID"])
        if key is None or key in ambiguous_keys:
            continue
        geometries[key] = feature
    by_segment = {}
    excluded = Counter()
    vehicles = Counter()
    trip_ids = set()
    duplicate_trip_ids = 0
    total = 0
    with FULL_CSV.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            total += 1
            trip_id = int(row["TripID"])
            duplicate_trip_ids += trip_id in trip_ids
            trip_ids.add(trip_id)
            vehicle = row["vehicleType"].strip()
            vehicles[vehicle] += 1
            if vehicle not in VEHICLES:
                excluded["unknown_vehicle"] += 1
            elif row["StartCenterlineType"].strip() != "street":
                excluded["nonstreet_start"] += 1
            else:
                key = segment_id(row["StartCenterlineID"])
                if key is None:
                    excluded["street_missing_id"] += 1
                else:
                    by_segment.setdefault(key, Counter())[vehicle] += 1
    if duplicate_trip_ids:
        raise ValueError(f"Found {duplicate_trip_ids:,} duplicated TripIDs; investigate before counting")
    rows = []
    unmatched = []
    for key, counts in sorted(by_segment.items()):
        n = sum(counts.values())
        if key not in geometries:
            reason = "ambiguous_network_id" if key in ambiguous_keys else "unmatched_street_id"
            excluded[reason] += n
            unmatched.append({"GBSID": key, "scooter": counts["scooter"], "bicycle": counts["bicycle"], "total_starts": n, "exclusion_reason": reason})
            continue
        attrs = geometries[key]["attributes"]
        rows.append({"GBSID": key, "street_name": attrs["STREET_O_NAME"] or "(unnamed)",
                     "from_street": attrs["STREET_F_NAME"] or "", "to_street": attrs["STREET_T_NAME"] or "",
                     "scooter": counts["scooter"], "bicycle": counts["bicycle"], "total_starts": n,
                     "scooter_share": counts["scooter"] / n, "bicycle_share": counts["bicycle"] / n})
    matched = sum(row["total_starts"] for row in rows)
    if matched + sum(excluded.values()) != total:
        raise ValueError("Join audit does not account for every trip")
    eligible = [row for row in rows if row["total_starts"] >= MIN_STARTS]
    if not eligible:
        raise ValueError("No segments meet the comparison threshold")
    eligible_starts = sum(row["total_starts"] for row in eligible)
    pooled = sum(row["scooter"] for row in eligible) / eligible_starts
    shares = [row["scooter_share"] for row in eligible]
    majority_scooter = sum(share > .5 for share in shares)
    majority_bicycle = sum(share < .5 for share in shares)
    fields = list(rows[0])
    write_csv(OUTPUT / "segment_vehicle_shares.csv", rows, fields)
    write_csv(OUTPUT / "unmatched_start_ids.csv", unmatched, ["GBSID", "scooter", "bicycle", "total_starts", "exclusion_reason"])
    comparison = compare_minimums(rows)
    write_csv(OUTPUT / "threshold_comparison.csv", comparison,
              ["minimum_starts", "segments", "trip_starts", "scooter_share"])
    audit = {"total_trips": total, "unique_trip_ids": len(trip_ids), "vehicles": dict(vehicles),
             "network_features": len(features), "unique_network_GBSID": len(geometries),
             "duplicated_network_GBSID": len(ambiguous_keys), "network_null_id_features": key_counts[None],
             "matched_starts": matched, "matched_segments": len(rows), "excluded": dict(excluded),
             "unmatched_distinct_ids": sum(row["exclusion_reason"] == "unmatched_street_id" for row in unmatched),
             "ambiguous_distinct_start_ids": sum(row["exclusion_reason"] == "ambiguous_network_id" for row in unmatched),
             "minimum_starts": MIN_STARTS,
             "eligible_segments": len(eligible), "eligible_starts": eligible_starts,
             "eligible_pooled_scooter_share": pooled, "eligible_median_segment_scooter_share": median(shares),
             "eligible_min_scooter_share": min(shares), "eligible_max_scooter_share": max(shares),
             "scooter_majority_segments": majority_scooter, "bicycle_majority_segments": majority_bicycle,
             "tied_segments": len(shares)-majority_scooter-majority_bicycle}
    (OUTPUT / "spatial_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    provenance = {"trip_source": json.loads((DATA / "item.json").read_text())["url"],
                  "street_source": STREET_URL, "network_crs": "EPSG:26915",
                  "files": {str(path.relative_to(DATA.parent.parent)): {
                      "bytes": path.stat().st_size,
                      "sha256": file_hash(path),
                  } for path in (FULL_CSV, NETWORK)}}
    (OUTPUT / "data_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    for mode, filename in (("share", "scooter_share_map.svg"), ("count", "trip_start_counts_map.svg")):
        make_map(features, rows, mode, filename)
    lines = ["# Street-segment vehicle comparison", "",
             "Research question: How do scooter and e-bike proportions vary across street segments where trips start, among matched segments with at least 100 recorded starts?", "",
             f"- Full CSV: {total:,} trips; {len(trip_ids):,} distinct TripIDs.",
             f"- Street network: {len(features):,} features; {len(ambiguous_keys):,} non-null GBSIDs repeat and are excluded from the join; {key_counts[None]:,} features lack a GBSID.",
             f"- Matched: {matched:,} trip starts on {len(rows):,} segments ({matched/total:.2%} of all trips).",
             f"- Excluded starts: {dict(excluded)}; unmatched distinct street IDs: {audit['unmatched_distinct_ids']:,}; ambiguous distinct trip-start IDs: {audit['ambiguous_distinct_start_ids']:,}.",
             f"- Comparison subset: {len(eligible):,} segments with at least {MIN_STARTS} starts, containing {eligible_starts:,} starts.",
             f"- Pooled scooter share in this subset: {pooled:.2%}; median segment scooter share (equal weight per segment): {median(shares):.2%}.",
             f"- Segment scooter shares range from {min(shares):.2%} to {max(shares):.2%}.",
             f"- Scooter-majority segments: {majority_scooter:,}; bicycle-majority: {majority_bicycle:,}; ties: {len(shares)-majority_scooter-majority_bicycle:,}.",
             "", "![Scooter share map](scooter_share_map.svg)", "", "![Trip start counts map](trip_start_counts_map.svg)", "",
             "## Examples: five lowest and five highest scooter shares", "",
             "| GBSID | Street | From | To | Scooter | Bicycle | Total | Scooter share |", "|---:|---|---|---|---:|---:|---:|---:|"]
    ordered = sorted(eligible, key=lambda row: (row["scooter_share"], row["GBSID"]))
    for row in ordered[:5] + ordered[-5:]:
        lines.append(f'| {row["GBSID"]} | {row["street_name"]} | {row["from_street"]} | {row["to_street"]} | {row["scooter"]:,} | {row["bicycle"]:,} | {row["total_starts"]:,} | {row["scooter_share"]:.2%} |')
    lines += ["", "## Minimum-start comparison", "",
              "All cutoffs use the same uniquely matched street segments. The main maps and results retain the 100-start minimum.", "",
              "| Minimum starts | Segments | Trip starts | Overall scooter share |",
              "|---:|---:|---:|---:|"]
    for row in comparison:
        share = "n/a" if row["scooter_share"] is None else f"{row['scooter_share']:.2%}"
        lines.append(f"| {row['minimum_starts']} | {row['segments']:,} | {row['trip_starts']:,} | {share} |")
    lines += ["", "The overall scooter share changes little across these cutoffs. The included segments and their individual percentages can still differ. The cutoff does not guarantee statistical reliability. Full values: [threshold_comparison.csv](threshold_comparison.csv).",
              "", "## Interpretation limits", "",
              "The unit is a recorded trip start, not a rider or a route. The 100-start threshold reduces the influence of very small denominators; it is a descriptive choice, not a statistical significance test. Segment-level summaries weight each eligible segment equally; pooled shares weight by trip count. No causal explanation or rider preference can be inferred. Shared-vehicle availability, pricing, land use, and program coverage were not controlled. Current street geometry may differ from the network used in 2025; unmatched and ambiguous IDs are listed rather than guessed. GBSIDs attached to multiple network features are excluded to avoid multiplying trip counts or assigning starts to an uncertain geometry.",
              "", "Sources: [trip table](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore), [PW Street Centerline](https://opendata.minneapolismn.gov/datasets/pw-street-centerline/about).", ""]
    (OUTPUT / "spatial_analysis.md").write_text("\n".join(lines))
    print(json.dumps(audit, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-network", action="store_true")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.download_network:
        download_network()
    analyze()


if __name__ == "__main__":
    main()
