"""Independently verify vehicle summaries against the full raw CSV, offline.

Run: python3 Analysis/verify_vehicle_comparison.py
Real-data expectations use statistics, not the analysis percentile helper.
"""

import copy
import csv
import math
import statistics
import tempfile
from collections import Counter
from pathlib import Path

from Codex_activity import FULL_CSV, OUTPUT


VEHICLES = ("scooter", "bicycle")
FIELDS = {"TripDuration": (60, "minutes"), "TripDistance": (1000, "kilometers")}
REASONS = ("missing", "nonnumeric", "nonfinite", "zero", "negative")


def reference_value(raw):
    """Independent numeric classification; no analysis functions are used."""
    if raw is None or raw.strip() == "":
        return None, "missing"
    try:
        value = float(raw)
    except ValueError:
        return None, "nonnumeric"
    if math.isnan(value) or math.isinf(value):
        return None, "nonfinite"
    if value <= 0:
        return None, "zero" if value == 0 else "negative"
    return value, "valid"


def raw_reference(path):
    values = {(v, f): [] for v in VEHICLES for f in FIELDS}
    excluded = {key: Counter() for key in values}
    totals, unexpected, seen = Counter(), Counter(), set()
    samples = {v: [] for v in VEHICLES}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not {"TripID", "vehicleType", "ObjectId", *FIELDS}.issubset(reader.fieldnames or []):
            raise ValueError("Reference CSV is missing required fields")
        for row in reader:
            if row["TripID"] is None or not row["TripID"].strip():
                raise ValueError("Reference CSV has a missing TripID")
            trip_id = int(row["TripID"])
            if trip_id in seen:
                raise ValueError("Reference CSV has a duplicate TripID")
            seen.add(trip_id)
            vehicle = row["vehicleType"]
            if vehicle not in VEHICLES:
                unexpected[vehicle or "<missing>"] += 1
                continue
            totals[vehicle] += 1
            for field in FIELDS:
                value, reason = reference_value(row[field])
                if reason == "valid":
                    values[vehicle, field].append(value)
                else:
                    excluded[vehicle, field][reason] += 1
            object_id = int(row["ObjectId"])
            sample = samples[vehicle]
            if len(sample) < 5 or object_id < int(sample[-1]["ObjectId"]):
                sample.append(row)
                sample.sort(key=lambda record: int(record["ObjectId"]))
                del sample[5:]
    expected = {}
    for key, raw_values in values.items():
        vehicle, field = key
        divisor, unit = FIELDS[field]
        ordered = sorted(raw_values)
        if len(ordered) >= 2:
            q25, _, q75 = statistics.quantiles(ordered, n=4, method="inclusive")
        elif ordered:
            q25 = q75 = ordered[0]
        else:
            q25 = q75 = None
        mid = statistics.median(ordered) if ordered else None
        result = {"total_trips": totals[vehicle], "valid_n": len(ordered), "unit": unit,
                  **{r: excluded[key][r] for r in REASONS}}
        result.update({name: None if value is None else value / divisor
                       for name, value in (("q25", q25), ("median", mid), ("q75", q75))})
        if len(ordered) + sum(result[r] for r in REASONS) != totals[vehicle]:
            raise ValueError("Reference accounting failed")
        expected[key] = result
    if sum(totals.values()) + sum(unexpected.values()) != len(seen):
        raise ValueError("Vehicle totals do not reconcile to raw rows")
    return expected, samples, len(seen), dict(unexpected)


def check_table(rows, expected):
    observed = {(row["vehicle"], row["measurement"]): row for row in rows}
    if len(observed) != len(rows) or observed.keys() != expected.keys():
        raise ValueError("Missing, duplicate, or unexpected summary groups")
    for key, reference in expected.items():
        row = observed[key]
        if row["unit"] != reference["unit"]:
            raise ValueError(f"Unit mismatch for {key}")
        for name in ("total_trips", "valid_n", *REASONS):
            if int(row[name]) != reference[name]:
                raise ValueError(f"Count mismatch for {key}: {name}")
        for name in ("q25", "median", "q75"):
            actual = None if row[name] in (None, "") else float(row[name])
            target = reference[name]
            if target is None:
                matches = actual is None
            else:
                matches = actual is not None and math.isclose(actual, target, rel_tol=0, abs_tol=1e-9)
            if not matches:
                raise ValueError(f"Summary mismatch for {key}: {name}")
        if reference["valid_n"] and not (float(row["q25"]) <= float(row["median"]) <= float(row["q75"])):
            raise ValueError(f"Percentiles out of order for {key}")


def self_checks():
    """Exercise meaningful edge cases and errors without changing real outputs."""
    from vehicle_comparison import summarize

    def rejected(action):
        try:
            action()
        except ValueError:
            return
        raise AssertionError("Expected a bad input/result to be rejected")

    with tempfile.TemporaryDirectory(prefix="vehicle_check_") as directory:
        path = Path(directory) / "fixture.csv"
        fields = ["TripID", "ObjectId", "vehicleType", "TripDuration", "TripDistance"]
        fixtures = [dict(TripID=i, ObjectId=i, vehicleType="scooter", TripDuration=value,
                         TripDistance=1000) for i, value in enumerate(
                             ("", "bad", "nan", "0", "-1", "60", "120", "180", "240"), 1)]
        fixtures[-1]["TripDistance"] = "0"  # Keep its valid duration independently.
        fixtures.append(dict(TripID=10, ObjectId=10, vehicleType="bicycle", TripDuration=600, TripDistance=2000))
        fixtures.append(dict(TripID=11, ObjectId=11, vehicleType="other", TripDuration=60, TripDistance=1000))

        def write(records, columns=fields):
            with path.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerows(records)

        write(fixtures)
        rows, audit = summarize(path)
        expected, _, _, _ = raw_reference(path)
        check_table(rows, expected)
        scooter = next(r for r in rows if r["vehicle"] == "scooter" and r["measurement"] == "TripDuration")
        assert scooter["valid_n"] == 4 and all(scooter[r] == 1 for r in REASONS)
        assert (scooter["q25"], scooter["median"], scooter["q75"]) == (1.75, 2.5, 3.25)
        distance = next(r for r in rows if r["vehicle"] == "scooter" and r["measurement"] == "TripDistance")
        assert distance["valid_n"] == 8 and distance["zero"] == 1
        assert audit["unexpected_vehicles"] == {"other": 1}
        bicycle = next(r for r in rows if r["vehicle"] == "bicycle" and r["measurement"] == "TripDuration")
        assert bicycle["q25"] == bicycle["median"] == bicycle["q75"] == 10
        changed = copy.deepcopy(rows)
        changed[0]["median"] += 1
        rejected(lambda: check_table(changed, expected))
        changed = copy.deepcopy(rows)
        changed[0]["valid_n"] += 1
        rejected(lambda: check_table(changed, expected))
        write(fixtures[:9])
        empty_rows, _ = summarize(path)
        empty_expected, _, _, _ = raw_reference(path)
        check_table(empty_rows, empty_expected)
        assert all(r["median"] is None and r["valid_n"] == 0 for r in empty_rows if r["vehicle"] == "bicycle")
        write(fixtures + [fixtures[0]])
        rejected(lambda: summarize(path))
        write([{**fixtures[0], "TripID": ""}])
        rejected(lambda: summarize(path))
        write([], ["TripID"])
        rejected(lambda: summarize(path))
    return "PASS: invalid values, independent measurement filters, unknown categories, inclusive quartiles, single-value and empty groups, missing/duplicate IDs, missing fields, and deliberately altered summaries/counts."


def main():
    checks = self_checks()
    expected, samples, total, unexpected = raw_reference(FULL_CSV)
    with (OUTPUT / "vehicle_comparison.csv").open(newline="") as file:
        rows = list(csv.DictReader(file))
    check_table(rows, expected)
    altered = copy.deepcopy(rows)
    altered[0]["median"] = float(altered[0]["median"]) + 1
    try:
        check_table(altered, expected)
    except ValueError:
        corruption = "PASS: changing the saved scooter-duration median by 1 minute was rejected."
    else:
        raise AssertionError("Deliberately altered real summary was accepted")
    lines = [
        "# Vehicle-comparison verification", "",
        "Expected results were recalculated directly from the full raw CSV, using `statistics.median` and `statistics.quantiles(method='inclusive')`. This does not reuse the analysis frequency-counter percentile calculation or derive expectations from the saved summary. It verifies processing of the same source, not the accuracy of vendor records.", "",
        f"Raw rows: **{total:,}**; unique nonmissing TripIDs confirmed; unexpected vehicle categories: `{unexpected}`. Vehicle counts and each measurement's valid/excluded counts reconcile.", "",
        "## Full-data comparison", "",
        "All four vehicle/measurement groups match: total trips, valid n, five exclusion counts, units, and all three quantiles. Numeric tolerance is absolute **1e-9**, using unrounded table values.", "",
        "| Vehicle | Unit | Valid n | Expected q25 | Expected median | Expected q75 | Result |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for (vehicle, _), result in expected.items():
        values = " | ".join("—" if result[k] is None else f"{result[k]:.9f}" for k in ("q25", "median", "q75"))
        lines.append(f"| {vehicle} | {result['unit']} | {result['valid_n']:,} | {values} | PASS |")
    lines.extend(["", "## Source-record unit checks", "",
                  "These are the first five source records per vehicle ordered by ObjectId, not a random sample. Raw seconds / 60 = minutes; raw meters / 1000 = kilometers. Invalid measurements would be marked excluded.", "",
                  "| Vehicle | ObjectId | TripID | Raw seconds | Minutes | Raw meters | Kilometers |",
                  "|---|---:|---:|---:|---:|---:|---:|"])
    for vehicle in VEHICLES:
        for row in samples[vehicle]:
            converted = []
            for field, (divisor, _) in FIELDS.items():
                value, _ = reference_value(row[field])
                converted.append("excluded" if value is None else f"{value / divisor:.9f}")
            lines.append(f"| {vehicle} | {row['ObjectId']} | {row['TripID']} | {row['TripDuration']} | {converted[0]} | {row['TripDistance']} | {converted[1]} |")
    lines.extend(["", "## Error-detection checks", "", checks, "", corruption, "",
                  "All checks passed. The source records support checking unit conversions; they do not establish the full-data medians. The separate full-data recalculation above checks those medians and quartiles.", "",
                  "Inspect the source-record conversions and full-data comparison yourself when writing your personal verification reflection. This report does not establish that you have done that review.", ""])
    (OUTPUT / "vehicle_comparison_verification.md").write_text("\n".join(lines))
    print(f"All four summary groups verified against {total:,} raw rows. {checks} {corruption}")


if __name__ == "__main__":
    main()
