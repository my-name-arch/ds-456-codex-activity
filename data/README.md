# Local data

Raw downloads are intentionally ignored by Git. The CSV is about 100 MB.

1. Download the CSV export from [Motorized Scooter and eBike Trips 2025](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore).
2. Save it as `data/exploration/_Motorized_Scooter_and_eBike_Trips_2025.csv`.
3. From the repository root, run:

```sh
python3 Analysis/Codex_activity.py
python3 Analysis/spatial_analysis.py --download-network
python3 Analysis/verify_spatial.py --fetch-reference
```

The first run needs internet access to the public ArcGIS services. It caches trip metadata, summaries, and an ordered 1,000-row preview, then downloads all PW Street Centerline features in pages and asks the service to project geometry to EPSG:26915. The preview is not a substitute for the full CSV.

With all cached inputs present, rerun offline:

```sh
python3 Analysis/Codex_activity.py
python3 Analysis/spatial_analysis.py
python3 Analysis/verify_spatial.py
python3 Analysis/vehicle_comparison.py
python3 Analysis/verify_vehicle_comparison.py
```

The last two commands run the follow-up comparison of duration and distance by vehicle, using the full CSV without a street-join filter. They save `vehicle_comparison.csv`, a report, two interval charts, and independent full-data verification with identified source-record conversions. Long valid trips are retained; missing and invalid measurements are accounted for separately.

All scripts use Python's standard library. Figures, tables, reference-query evidence, and reports are saved under `Analysis/outputs/`. `data_provenance.json` records SHA-256 hashes of the full CSV and merged street geometry used for the spatial results. `threshold_comparison.csv` compares minimums of 50, 100, and 200 starts without changing the main 100-start maps. The saved verification reference covers four mapped segments and one ambiguous-ID exclusion and is tracked under `Analysis/outputs/verification_reference.json` so readers can inspect it without downloading raw data.

The street layer is current, not necessarily a 2025 snapshot. Repeated non-null GBSIDs and unmatched trip IDs are excluded explicitly. A future export or updated service may produce different counts; do not mix updated data with cached summaries without checking consistency.
