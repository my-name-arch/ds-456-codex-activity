"""Initial exploration of Minneapolis scooter/e-bike trips (standard library only).

Run `python3 Analysis/Codex_activity.py` from any directory. Responses are cached
under data/; pass --refresh to fetch them again. Summaries cover the whole table;
the CSV contains only the first 1,000 records by ObjectId, NOT a random sample.
"""

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "exploration"
OUTPUT = ROOT / "Analysis" / "outputs"
ITEM = "https://www.arcgis.com/sharing/rest/content/items/d9a1f322528447ff9c1bc86e5d0895c5"
FULL_CSV = DATA / "_Motorized_Scooter_and_eBike_Trips_2025.csv"

FIELD_ROLES = {
    "TripID": "Trip identifier (not a measurement)",
    "ObjectId": "ArcGIS row identifier (not a measurement)",
    "vehicleType": "Category: scooter or bicycle",
    "TripDuration": "Numeric measurement, seconds",
    "TripDistance": "Numeric measurement, meters",
    "StartTime": "Datetime, rounded to half hour; service declares UTC",
    "EndTime": "Datetime, rounded to half hour; service declares UTC",
    "StartCenterlineID": "Start segment join key (not a coordinate)",
    "EndCenterlineID": "End segment join key (not a coordinate)",
    "StartCenterlineType": "Category: street or trail",
    "EndCenterlineType": "Category: street or trail",
}


def bar_chart(filename, title, subtitle, records):
    """Write a labeled horizontal count chart without extra dependencies."""
    height = 120 + 48 * len(records)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="{height}" viewBox="0 0 1050 {height}">',
             f'<title>{escape(title)}</title>',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" fill="#172b4d">',
             f'<text x="20" y="30" font-size="22">{escape(title)}</text>',
             f'<text x="20" y="55" font-size="13">{escape(subtitle)}</text>']
    maximum = max((count for _, count in records), default=0) or 1
    for i, (label, count) in enumerate(records):
        y = 80 + i * 48
        parts.extend([f'<text x="20" y="{y + 20}" font-size="14">{escape(label)}</text>',
                      f'<rect x="230" y="{y}" width="{560 * count / maximum:.1f}" height="28" fill="#276fbf"/>',
                      f'<text x="810" y="{y + 20}" font-size="14">{count:,}</text>'])
    parts.extend([f'<text x="230" y="{height - 12}" font-size="13">Bar length: trip count (starts at zero); values shown at right</text>',
                  '</g></svg>'])
    (OUTPUT / filename).write_text("\n".join(parts))


def percentile(counts, probability):
    """Exact linear-interpolated quantile from frequencies, using rank (n-1)*p."""
    n = sum(counts.values())
    if not n:
        return None
    rank = (n - 1) * probability
    lower, upper = math.floor(rank), math.ceil(rank)
    cumulative = 0
    low_value = None
    for value, count in sorted(counts.items()):
        cumulative += count
        if low_value is None and cumulative > lower:
            low_value = value
        if cumulative > upper:
            return low_value + (value - low_value) * (rank - lower)


def explore_full_csv(expected_total, field_names):
    """Stream the full local export; preserve missing and invalid-value counts."""
    if not FULL_CSV.exists():
        return ["", "Full CSV not found; distribution charts require the full export at " + str(FULL_CSV) + "."]
    missing = Counter()
    invalid = Counter()
    distributions = {field: Counter() for field in ("TripDuration", "TripDistance")}
    total = 0
    with FULL_CSV.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != field_names:
            raise ValueError("Full CSV fields do not match the service schema")
        for row in reader:
            total += 1
            for field in field_names:
                if row[field] is None or not row[field].strip():
                    missing[field] += 1
            for field, counts in distributions.items():
                if row[field] is None or not row[field].strip():
                    continue
                try:
                    value = float(row[field])
                except ValueError:
                    invalid[field] += 1
                    continue
                if not math.isfinite(value):
                    invalid[field] += 1
                else:
                    counts[value] += 1
    if total != expected_total:
        raise ValueError(f"Local CSV has {total:,} rows; cached service count is {expected_total:,}. Check export completeness or refresh the API cache.")
    lines = ["", "## Full local CSV: distributions and quality", "",
             f"Analyzed all **{total:,}** local CSV rows; row count agrees with the cached API count.",
             "Missing means an empty or whitespace-only CSV cell. Numeric parse errors and nonfinite values are reported separately; valid zeros and negative values are retained.",
             "", "| Measurement | Valid n | Median | 25th percentile | 75th percentile | 95th percentile | Zero | Negative | Invalid |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    figures = []
    for field, divisor, label, bounds, filename in (
        ("TripDuration", 60, "Duration (minutes)", [0, 5, 10, 15, 30, 60, math.inf], "duration_distribution.svg"),
        ("TripDistance", 1000, "Distance (kilometers)", [0, 1, 2, 3, 5, 10, math.inf], "distance_distribution.svg"),
    ):
        counts = distributions[field]
        n = sum(counts.values())
        if n + missing[field] + invalid[field] != total:
            raise ValueError(f"Numeric quality counts do not reconcile for {field}")
        quantiles = [percentile(counts, p) for p in (0.5, 0.25, 0.75, 0.95)]
        values = " | ".join("missing" if value is None else f"{value / divisor:.2f}" for value in quantiles)
        lines.append(f"| {label} | {n:,} | {values} | {counts[0]:,} | {sum(c for v, c in counts.items() if v < 0):,} | {invalid[field]:,} |")
        bins = [("Below 0", sum(c for v, c in counts.items() if v < 0))]
        for low, high in zip(bounds, bounds[1:]):
            name = f"{low:g} to <{high:g}" if math.isfinite(high) else f"{low:g}+"
            bins.append((name, sum(c for v, c in counts.items() if low <= v / divisor < high)))
        if sum(count for _, count in bins) != n:
            raise ValueError(f"Distribution bins do not reconcile for {field}")
        bar_chart(filename, f"Trip {label.lower()} distribution", f"Full CSV; valid n = {n:,}; missing = {missing[field]:,}; invalid = {invalid[field]:,}", bins)
        figures.extend(["", f"![{label} distribution]({filename})", ""])
    lines.extend(figures)
    bar_chart("missing_values.svg", "Missing values by field", f"Full CSV, {total:,} rows; empty/whitespace cells; records retained", [(f, missing[f]) for f in field_names])
    lines.extend(["Quantiles use linear interpolation at rank (n − 1) × p. Means and medians describe different aspects of the distribution; inspect the upper tail before choosing a summary.",
                  "", "![Missing values by field](missing_values.svg)", "",
                  "| Field | Missing CSV cells | Percent of all rows |", "|---|---:|---:|"])
    lines.extend(f"| {field} | {missing[field]:,} | {missing[field] / total:.2%} |" for field in field_names)
    return lines


def fetch(name, url, params, refresh):
    """Cache successful responses; surface API errors instead of summarizing them."""
    path = DATA / f"{name}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    # POST queries to keep long statistics expressions out of the URL.
    encoded = urlencode({"f": "json", **params})
    address = url if url.endswith("/query") else url + "?" + encoded
    body = encoded.encode() if url.endswith("/query") else None
    with urlopen(address, data=body, timeout=90) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{name}: {result['error']}")
    path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def statistic(field, kind, alias):
    return {"statisticType": kind, "onStatisticField": field, "outStatisticFieldName": alias}


def iso_date(value):
    if value is None:
        return "missing"
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Replace cached API responses")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    item = fetch("item", ITEM, {}, args.refresh)
    layer_url = item["url"] + "/0"
    layer = fetch("layer", layer_url, {}, args.refresh)

    def query(name, **params):
        return fetch(name, layer_url + "/query", {"where": "1=1", "returnGeometry": "false", **params}, args.refresh)

    total = query("count", returnCountOnly="true")["count"]
    stats = [statistic(f["name"], "count", f"{f['name']}_count") for f in layer["fields"]]
    for field in ("TripDuration", "TripDistance", "StartTime", "EndTime"):
        for kind in ("min", "max"):
            stats.append(statistic(field, kind, f"{field}_{kind}"))
    for field in ("TripDuration", "TripDistance"):
        stats.append(statistic(field, "avg", f"{field}_avg"))
    summary = query("summary", outStatistics=json.dumps(stats))["features"][0]["attributes"]

    groups = {}
    for field in ("vehicleType", "StartCenterlineType", "EndCenterlineType"):
        group_stats = [statistic("ObjectId", "count", "trips")]
        if field != "vehicleType":
            group_stats.append(statistic(field.replace("Type", "ID"), "count", "location_ids"))
        result = query(field + "_counts", groupByFieldsForStatistics=field,
                       outStatistics=json.dumps(group_stats),
                       orderByFields="trips DESC")
        if result.get("exceededTransferLimit"):
            raise RuntimeError(f"Incomplete grouped query: {field}")
        groups[field] = [feature["attributes"] for feature in result["features"]]
        if sum(row["trips"] for row in groups[field]) != total:
            raise RuntimeError(f"Grouped counts for {field} do not match table count")

    sample = query("first_1000", outFields="*", orderByFields="ObjectId ASC",
                   resultRecordCount=min(1000, layer["maxRecordCount"]))
    rows = [feature["attributes"] for feature in sample["features"]]
    with (DATA / "first_1000.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[f["name"] for f in layer["fields"]])
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Initial dataset exploration", "", f"Source: [{item['title'].strip()}]({layer_url})",
             "", f"- Rows (whole table): **{total:,}**",
             f"- Columns: **{len(layer['fields'])}**",
             f"- ArcGIS layer type: **{layer['type']}** (no geometry).",
             f"- StartTime range (service UTC): {iso_date(summary['StartTime_min'])} to {iso_date(summary['StartTime_max'])}.",
             f"- EndTime range (service UTC): {iso_date(summary['EndTime_min'])} to {iso_date(summary['EndTime_max'])}.",
             "", "## Fields and missing values (whole table)", "",
             "| Field | ArcGIS storage type | Meaning / analytical role | Null values |", "|---|---|---|---:|"]
    for field in layer["fields"]:
        name = field["name"]
        lines.append(f"| {name} | {field['type']} | {FIELD_ROLES.get(name, 'Undocumented')} | {total - summary[name + '_count']:,} |")
    lines += ["", "Counts detect nulls, not blank strings, sentinel IDs, or invalid values.",
              "", "## Duration and distance (whole table, nulls excluded)", "",
              "| Variable | Minimum | Mean | Maximum |", "|---|---:|---:|---:|"]
    for field, label, divisor in (("TripDuration", "Duration (minutes)", 60),
                                  ("TripDistance", "Distance (kilometers)", 1000)):
        values = [summary[f"{field}_{kind}"] for kind in ("min", "avg", "max")]
        text_values = ["missing" if value is None else f"{value / divisor:,.2f}" for value in values]
        lines.append(f"| {label} | " + " | ".join(text_values) + " |")
    for field, records in groups.items():
        has_ids = field != "vehicleType"
        lines += ["", f"## {field} (whole table)", "",
                  "| Category | Trips | Share |" + (" Null location IDs |" if has_ids else ""),
                  "|---|---:|---:|" + ("---:|" if has_ids else "")]
        for row in records:
            label = "(null)" if row[field] is None else row[field]
            missing = f" {row['trips'] - row['location_ids']:,} |" if has_ids else ""
            lines.append(f"| {label} | {row['trips']:,} | {row['trips'] / total:.2%} |" + missing)
    lines += explore_full_csv(total, [field["name"] for field in layer["fields"]])
    lines += ["", "Interpretation and limits are kept in the [activity notes](../../Codex_Activity.md#interpretation-and-limits).",
              "", "![Trip counts by vehicle type](vehicle_counts.svg)", ""]
    (OUTPUT / "exploration.md").write_text("\n".join(lines))

    bar_chart("vehicle_counts.svg", "Minneapolis scooter and e-bike trips",
              "Whole-table counts by recorded vehicle type",
              [(str(row["vehicleType"]), row["trips"]) for row in groups["vehicleType"]])
    print("\n".join(lines))


if __name__ == "__main__":
    main()
