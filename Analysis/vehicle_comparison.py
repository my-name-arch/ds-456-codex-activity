"""Compare recorded duration and distance by vehicle; no street-join filter.

Run: python3 Analysis/vehicle_comparison.py
Uses the full local export, offline, and retains valid long trips.
"""

import csv
import hashlib
import json
import math
from collections import Counter
from html import escape

from Codex_activity import FULL_CSV, OUTPUT, percentile


VEHICLES = ("scooter", "bicycle")
MEASUREMENTS = (
    ("TripDuration", "minutes", 60, "Duration"),
    ("TripDistance", "kilometers", 1000, "Distance"),
)
REASONS = ("missing", "nonnumeric", "nonfinite", "zero", "negative")
COLUMNS = ("vehicle", "measurement", "unit", "total_trips", "valid_n",
           *REASONS, "q25", "median", "q75")


def classify(raw):
    """Give each measurement exactly one valid/excluded classification."""
    if raw is None or not raw.strip():
        return "missing", None
    try:
        value = float(raw)
    except ValueError:
        return "nonnumeric", None
    if not math.isfinite(value):
        return "nonfinite", None
    if value == 0:
        return "zero", None
    if value < 0:
        return "negative", None
    return "valid", value


def summarize(path):
    totals, unknown, seen = Counter(), Counter(), set()
    counts = {(v, f): Counter() for v in VEHICLES for f, *_ in MEASUREMENTS}
    excluded = {key: Counter() for key in counts}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"TripID", "vehicleType", *(f for f, *_ in MEASUREMENTS)}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV is missing required comparison fields")
        for row in reader:
            raw_id = row["TripID"]
            if raw_id is None or not raw_id.strip():
                raise ValueError("Missing TripID")
            trip_id = int(raw_id)
            if trip_id in seen:
                raise ValueError(f"Duplicate TripID: {trip_id}")
            seen.add(trip_id)
            vehicle = row["vehicleType"]
            if vehicle not in VEHICLES:
                unknown[vehicle or "<missing>"] += 1
                continue
            totals[vehicle] += 1
            for field, *_ in MEASUREMENTS:
                reason, value = classify(row[field])
                if reason == "valid":
                    counts[vehicle, field][value] += 1
                else:
                    excluded[vehicle, field][reason] += 1
    rows = []
    for vehicle in VEHICLES:
        for field, unit, divisor, _ in MEASUREMENTS:
            distribution = counts[vehicle, field]
            row = dict(vehicle=vehicle, measurement=field, unit=unit,
                       total_trips=totals[vehicle], valid_n=sum(distribution.values()))
            row.update({reason: excluded[vehicle, field][reason] for reason in REASONS})
            for name, p in (("q25", .25), ("median", .5), ("q75", .75)):
                result = percentile(distribution, p)
                row[name] = None if result is None else result / divisor
            if row["valid_n"] + sum(row[r] for r in REASONS) != row["total_trips"]:
                raise ValueError("Measurement accounting failed")
            rows.append(row)
    return rows, {"total_rows": len(seen), "unexpected_vehicles": dict(unknown)}


def interval_chart(rows, field, title, unit):
    """Shared linear axis; the interval is the IQR, not a confidence interval."""
    selected = [row for row in rows if row["measurement"] == field]
    maximum = max((row["q75"] or 0 for row in selected), default=0) * 1.25 or 1
    left, width = 220, 680
    x = lambda value: left + width * value / maximum
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="355" viewBox="0 0 1050 355">',
        f'<title>{escape(title)} by vehicle</title>',
        '<desc>Lines show the 25th to 75th percentile; dots show medians. Valid long trips are retained.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" fill="#172b4d">',
        f'<text x="24" y="32" font-size="23">{escape(title)} by vehicle</text>',
        '<text x="24" y="58" font-size="14">Full CSV; streets and trails; dot = median; line = middle 50% of recorded trips</text>',
    ]
    for tick in range(6):
        value = maximum * tick / 5
        position = x(value)
        parts.extend([
            f'<line x1="{position:.2f}" x2="{position:.2f}" y1="85" y2="245" stroke="#e2e8f0"/>',
            f'<text x="{position:.2f}" y="268" text-anchor="middle" font-size="13">{value:.2f}</text>',
        ])
    for index, row in enumerate(selected):
        y = 122 + index * 93
        label = "Scooter" if row["vehicle"] == "scooter" else "E-bike (bicycle)"
        parts.extend([
            f'<text x="24" y="{y}" font-size="16">{label}</text>',
            f'<text x="24" y="{y + 21}" font-size="13">valid n = {row["valid_n"]:,}</text>',
        ])
        if row["median"] is None:
            parts.append(f'<text x="{left}" y="{y}" font-size="14">No valid measurements</text>')
            continue
        parts.extend([
            f'<line x1="{x(row["q25"]):.2f}" x2="{x(row["q75"]):.2f}" y1="{y}" y2="{y}" stroke="#276fbf" stroke-width="9"/>',
            f'<circle cx="{x(row["median"]):.2f}" cy="{y}" r="7" fill="#172b4d"/>',
            f'<text x="{x(row["median"]):.2f}" y="{y + 29}" text-anchor="middle" font-size="13">median {row["median"]:.2f}; middle 50% {row["q25"]:.2f}–{row["q75"]:.2f}</text>',
        ])
    parts.extend([
        f'<text x="560" y="298" text-anchor="middle" font-size="15">{escape(title)} ({unit}); shared axis starts at zero</text>',
        '<text x="24" y="330" font-size="13">Intervals describe trip variation, not uncertainty; tails are retained in calculations and extend beyond the intervals.</text>',
        '</g></svg>',
    ])
    return "\n".join(parts) + "\n"


def main():
    rows, audit = summarize(FULL_CSV)
    digest = hashlib.sha256()
    with FULL_CSV.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "vehicle_comparison.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Duration and distance by vehicle", "",
        "This follow-up was reviewed in Plan mode before implementation. It supplements the spatial analysis.", "",
        f"The full CSV has **{audit['total_rows']:,}** unique, nonmissing TripIDs. Both street and trail trips are included, including records excluded from mapping. No 100-start threshold or street join is applied.", "",
        "The source categories are `scooter` and `bicycle`; the city describes bicycles as e-bikes. Each measurement independently excludes missing, nonnumeric, nonfinite, zero, and negative values. All valid positive measurements are retained, including unusually long trips. Duration uses the recorded seconds, not differences between rounded timestamps.", "",
        f"Unexpected vehicle categories (excluded): `{json.dumps(audit['unexpected_vehicles'], sort_keys=True)}`.", "",
        "| Vehicle | Measurement | Total trips | Valid n | 25th percentile | Median | 75th percentile |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        values = " | ".join("—" if row[k] is None else f"{row[k]:.2f}" for k in ("q25", "median", "q75"))
        lines.append(f"| {row['vehicle']} | {row['unit']} | {row['total_trips']:,} | {row['valid_n']:,} | {values} |")
    lines.append("")
    for field, unit, _, title in MEASUREMENTS:
        medians = {row["vehicle"]: row["median"] for row in rows if row["measurement"] == field}
        if all(value is not None for value in medians.values()):
            difference = medians["bicycle"] - medians["scooter"]
            lines.append(f"{title}: the e-bike median minus the scooter median is **{difference:.2f} {unit}**. This is a difference between group medians, not paired trips.")
    lines.extend(["", "## Measurement exclusions", "",
                  "| Vehicle | Measurement | Missing | Nonnumeric | Nonfinite | Zero | Negative |",
                  "|---|---|---:|---:|---:|---:|---:|"])
    for row in rows:
        values = " | ".join(str(row[r]) for r in REASONS)
        lines.append(f"| {row['vehicle']} | {row['measurement']} | {values} |")
    for field, unit, _, title in MEASUREMENTS:
        filename = "vehicle_duration.svg" if field == "TripDuration" else "vehicle_distance.svg"
        (OUTPUT / filename).write_text(interval_chart(rows, field, title, unit))
        lines.extend(["", f"![{title} by vehicle]({filename})"])
    lines.extend([
        "", "Quantiles use linear interpolation at rank (n − 1) × p. Chart intervals show the middle 50%, not confidence intervals or the full range. Values describe recorded trips; rider preferences, trip purposes, and causes of differences were not tested.", "",
        "Exact values and all exclusion counts: [vehicle_comparison.csv](vehicle_comparison.csv). Independent recalculation and source-record conversions: [vehicle_comparison_verification.md](vehicle_comparison_verification.md).", "",
        f"Source CSV SHA-256: `{digest.hexdigest()}`.", "",
    ])
    (OUTPUT / "vehicle_comparison.md").write_text("\n".join(lines))
    print(f"Compared {audit['total_rows']:,} trips; saved table, report, and two charts.")


if __name__ == "__main__":
    main()
