import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

files = sorted(RAW.glob("*.csv"))

print(f"CSV files found: {len(files)}")
if not files:
    print(f"No CSV files found in: {RAW}")
    raise SystemExit(0)

tracks = []
total_rows = 0

for file in files:
    try:
        df = pd.read_csv(file)

        if df.empty:
            continue

        total_rows += len(df)

        df["iceberg_id"] = file.stem

        for target, candidates in {
            "latitude": [
                "latitude", "lat",
                "sass_1", "nic_1", "ascat_1", "ers_1",
                "qscat_1", "seawinds_1", "oscat_1", "nscat_1"
            ],
            "longitude": [
                "longitude", "lon",
                "sass_2", "nic_2", "ascat_2", "ers_2",
                "qscat_2", "seawinds_2", "oscat_2", "nscat_2"
            ],
        }.items():
            source = next((col for col in candidates if col in df.columns), None)
            if source is None:
                raise KeyError(f"{target}")
            df[target] = pd.to_numeric(df[source], errors="coerce")

        df["date"] = pd.to_datetime(
            df["date"].astype(str),
            format="%Y%j",
            errors="coerce"
        )

        df = df.dropna(
            subset=["date", "latitude", "longitude"]
        )

        df = df.sort_values("date")

        if len(df) >= 2:
            duration = (
                df["date"].iloc[-1] -
                df["date"].iloc[0]
            ).days

            tracks.append({
                "id": file.stem,
                "observations": len(df),
                "start": df["date"].iloc[0],
                "end": df["date"].iloc[-1],
                "duration_days": duration,
                "lat_min": df["latitude"].min(),
                "lat_max": df["latitude"].max(),
                "lon_min": df["longitude"].min(),
                "lon_max": df["longitude"].max()
            })

    except Exception as e:
        print(f"Skipped {file.name}: {e}")

summary = pd.DataFrame(tracks)

print("\n" + "=" * 50)
print("ICEBERG DATABASE SUMMARY")
print("=" * 50)

print(f"Total CSV files       : {len(files)}")
print(f"Usable iceberg tracks : {len(summary)}")
print(f"Total raw observations: {total_rows}")

if len(summary):

    print(
        f"Total usable observations: "
        f"{summary['observations'].sum()}"
    )

    print(
        f"Date range: "
        f"{summary['start'].min().date()} - "
        f"{summary['end'].max().date()}"
    )

    print(
        f"Median observations/track: "
        f"{summary['observations'].median():.0f}"
    )

    print(
        f"Median track duration: "
        f"{summary['duration_days'].median():.0f} days"
    )

    print(
        f"Max track duration: "
        f"{summary['duration_days'].max():.0f} days"
    )

    print("\nTrack length distribution:")

    bins = [0, 7, 30, 90, 180, 365, np.inf]
    labels = [
        "<7 days",
        "7–30 days",
        "30–90 days",
        "90–180 days",
        "180–365 days",
        ">365 days"
    ]

    distribution = pd.cut(
        summary["duration_days"],
        bins=bins,
        labels=labels,
        right=False
    ).value_counts().sort_index()

    for label, count in distribution.items():
        print(f"{str(label):12s}: {count}")

    print("\nTop 10 longest tracks:")

    print(
        summary
        .sort_values("duration_days", ascending=False)
        [["id", "observations", "start", "end", "duration_days"]]
        .head(10)
        .to_string(index=False)
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = PROCESSED_DIR / "track_summary.csv"
    summary.to_csv(output_path, index=False)

    print(f"\nSaved: {output_path}")