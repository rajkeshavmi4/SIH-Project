from pathlib import Path
import pandas as pd
import numpy as np

RAW = Path("data/raw")
OUT = Path("data/processed")

MIN_OBSERVATIONS = 7

# Priority order for coordinate sources (satellite sensors)
# Based on availability and expected measurement quality
COORD_SOURCES = [
    ("sass_1", "sass_2", "sass_3"),      # SASS - early satellite data
    ("qscat_1", "qscat_2", "qscat_3"),   # QuikSCAT/SeaWinds scatterometer
    ("ascat_1", "ascat_2", "ascat_3"),   # ASCAT advanced scatterometer
    ("ers_1", "ers_2", "ers_3"),         # ERS European Remote Sensing
    ("oscat_1", "oscat_2", "oscat_3"),   # OSCAT
    ("nscat_1", "nscat_2", "nscat_3"),   # NSCAT
    ("seawinds_1", "seawinds_2", "seawinds_3"),  # SeaWinds
    ("nic_1", "nic_2", "nic_3"),         # NIC - National Ice Center derived
]

rows = []
stats = {
    "files": 0,
    "usable": 0,
    "skipped": 0,
    "observations": 0,
    "by_source": {}
}

print("=" * 60)
print("ICEBERG TRAJECTORY DATASET - COORDINATE ANALYSIS")
print("=" * 60)

for file in sorted(RAW.glob("*.csv")):
    stats["files"] += 1

    try:
        df = pd.read_csv(file)

        # Find which coordinate source is available in this file
        coord_source = None
        lat_col, lon_col, conf_col = None, None, None
        
        for lat_c, lon_c, conf_c in COORD_SOURCES:
            if lat_c in df.columns and lon_c in df.columns:
                coord_source = lat_c.rsplit("_", 1)[0]  # Extract sensor name
                lat_col, lon_col, conf_col = lat_c, lon_c, conf_c
                break

        if coord_source is None:
            stats["skipped"] += 1
            continue

        # Extract required columns
        cols_to_keep = ["date", lat_col, lon_col]
        if conf_col in df.columns:
            cols_to_keep.append(conf_col)
        
        df = df[cols_to_keep].copy()

        # Parse date
        df["date"] = pd.to_datetime(
            df["date"].astype(str).str.strip(),
            format="%Y%j",
            errors="coerce"
        )

        # Validate dates are reasonable (between 1970 and 2050)
        valid_date_range = (df["date"] >= pd.Timestamp("1970-01-01")) & \
                           (df["date"] <= pd.Timestamp("2050-12-31"))
        df = df[valid_date_range]

        if len(df) == 0:
            stats["skipped"] += 1
            continue
        df["latitude"] = pd.to_numeric(df[lat_col], errors="coerce")
        df["longitude"] = pd.to_numeric(df[lon_col], errors="coerce")

        # Remove rows with missing coordinates or dates
        df = df.dropna(subset=["date", "latitude", "longitude"])

        if len(df) == 0:
            stats["skipped"] += 1
            continue

        # Sanity check: latitude should be between -90 and 90
        df = df[df["latitude"].between(-90, 90)]
        
        # Sanity check: longitude should be between -180 and 180
        df = df[df["longitude"].between(-180, 180)]

        if len(df) == 0:
            stats["skipped"] += 1
            continue

        # Remove duplicates by date and sort
        df = (
            df
            .drop_duplicates("date")
            .sort_values("date")
            .reset_index(drop=True)
        )

        # Apply minimum observations threshold
        if len(df) < MIN_OBSERVATIONS:
            stats["skipped"] += 1
            continue

        # Prepare final output
        df["iceberg_id"] = file.stem
        df["coord_source"] = coord_source

        df = df[
            [
                "iceberg_id",
                "date",
                "latitude",
                "longitude",
                "coord_source"
            ]
        ]

        rows.append(df)

        # Track statistics
        stats["usable"] += 1
        stats["observations"] += len(df)
        if coord_source not in stats["by_source"]:
            stats["by_source"][coord_source] = 0
        stats["by_source"][coord_source] += 1

    except Exception as e:
        print(f"ERROR reading {file.name}: {e}")
        stats["skipped"] += 1

print("\n" + "=" * 60)
print("COORDINATE SOURCE DISTRIBUTION")
print("=" * 60)
for source in sorted(stats["by_source"].keys()):
    count = stats["by_source"][source]
    print(f"  {source:15s}: {count:3d} files")


if not rows:
    raise RuntimeError("No usable iceberg tracks found.")

tracks = pd.concat(
    rows,
    ignore_index=True
)

# Print summary statistics
print("\n" + "=" * 60)
print("FILTERING & AGGREGATION SUMMARY")
print("=" * 60)
print(f"CSV files processed       : {stats['files']}")
print(f"Usable tracks extracted   : {stats['usable']}")
print(f"Skipped tracks            : {stats['skipped']}")
print(f"Total observations        : {stats['observations']}")

# Analysis of final dataset
print("\n" + "=" * 60)
print("FINAL DATASET STATISTICS")
print("=" * 60)
print(f"Unique icebergs           : {tracks['iceberg_id'].nunique()}")
print(f"Date range                : {tracks['date'].min().strftime('%Y-%m-%d')} → {tracks['date'].max().strftime('%Y-%m-%d')}")
print(f"Latitude range            : {tracks['latitude'].min():.2f}° → {tracks['latitude'].max():.2f}°")
print(f"Longitude range           : {tracks['longitude'].min():.2f}° → {tracks['longitude'].max():.2f}°")

obs_per_track = tracks.groupby('iceberg_id').size()
print(f"Observations per track    : min={obs_per_track.min()}, median={obs_per_track.median():.0f}, max={obs_per_track.max()}")

# Save output
OUT.mkdir(parents=True, exist_ok=True)
output_file = OUT / "master_trajectories.csv"
tracks.to_csv(output_file, index=False)

print("\n" + "=" * 60)
print(f"✓ Saved → {output_file}")
print("=" * 60)