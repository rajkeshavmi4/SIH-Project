from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT = PROJECT_ROOT / "data" / "processed" / "trajectory_features.csv"
OUT = PROJECT_ROOT / "data" / "processed" / "iceberg_ml"

SEQ_LEN = 7
HORIZONS = [1, 2, 3]
SEED = 42
EARTH_RADIUS_KM = 6371.0088

FEATURES = [
    "latitude",
    "longitude",
    "delta_lat",
    "delta_lon",
    "speed_kmh"
]

rng = np.random.default_rng(SEED)


def displacement_km(origin, destination):
    lat1, lon1 = np.radians(origin)
    lat2, lon2 = np.radians(destination)
    dlon = (lon2 - lon1 + np.pi) % (2 * np.pi) - np.pi
    north = (lat2 - lat1) * EARTH_RADIUS_KM
    east = dlon * EARTH_RADIUS_KM * np.cos(lat1)
    return np.array([north, east], dtype=np.float32)

df = pd.read_csv(INPUT, parse_dates=["date"])
df["delta_lon"] = (df["delta_lon"] + 180.0) % 360.0 - 180.0
df = df.sort_values(["track_id", "date"]).reset_index(drop=True)

tracks = []

for track_id, g in df.groupby("track_id", sort=False):
    g = g.dropna(subset=FEATURES).reset_index(drop=True)

    if len(g) < SEQ_LEN + max(HORIZONS):
        continue

    tracks.append(track_id)

track_to_iceberg = df.groupby("track_id")["iceberg_id"].first().to_dict()
iceberg_tracks = defaultdict(list)
for track_id in tracks:
    iceberg_tracks[track_to_iceberg[track_id]].append(track_id)

icebergs = np.array(sorted(iceberg_tracks))
rng.shuffle(icebergs)

n = len(icebergs)
n_train = int(n * 0.70)
n_val = int(n * 0.15)

train_tracks = {track_id for iceberg_id in icebergs[:n_train] for track_id in iceberg_tracks[iceberg_id]}
val_tracks = {track_id for iceberg_id in icebergs[n_train:n_train + n_val] for track_id in iceberg_tracks[iceberg_id]}
test_tracks = {track_id for iceberg_id in icebergs[n_train + n_val:] for track_id in iceberg_tracks[iceberg_id]}

split_icebergs = [
    {track_to_iceberg[track_id] for track_id in allowed}
    for allowed in (train_tracks, val_tracks, test_tracks)
]
if set.intersection(*split_icebergs):
    raise RuntimeError("Iceberg identities overlap between dataset splits.")

print(f"Icebergs: {n}")
print(f"Train tracks: {len(train_tracks)}")
print(f"Val tracks  : {len(val_tracks)}")
print(f"Test tracks : {len(test_tracks)}")

splits = {
    "train": train_tracks,
    "val": val_tracks,
    "test": test_tracks
}

OUT.mkdir(parents=True, exist_ok=True)

for split, allowed in splits.items():

    X = []
    Y = {h: [] for h in HORIZONS}
    metadata = []

    for track_id, g in df.groupby("track_id", sort=False):

        if track_id not in allowed:
            continue

        g = g.dropna(subset=FEATURES).reset_index(drop=True)

        values = g[FEATURES].values.astype(np.float32)
        latlon = g[["latitude", "longitude"]].values.astype(np.float32)

        dates = g["date"].to_numpy(dtype="datetime64[D]")
        for i in range(SEQ_LEN, len(g) - max(HORIZONS) + 1):
            window_dates = dates[i - SEQ_LEN:i + max(HORIZONS)]
            if not np.all(np.diff(window_dates).astype("timedelta64[D]").astype(int) == 1):
                continue

            x = values[i - SEQ_LEN:i]

            X.append(x)

            for h in HORIZONS:
                future = latlon[i + h - 1]
                current = latlon[i - 1]
                Y[h].append(displacement_km(current, future))

            metadata.append([
                track_id,
                g["iceberg_id"].iloc[i],
                g["date"].iloc[i - 1],
                g["date"].iloc[i]
            ])

    X = np.asarray(X, dtype=np.float32)

    np.save(
        OUT / f"X_{split}.npy",
        X
    )

    for h in HORIZONS:
        np.save(
            OUT / f"Y_{h}d_{split}.npy",
            np.asarray(Y[h], dtype=np.float32)
        )

    pd.DataFrame(
        metadata,
        columns=[
            "track_id",
            "iceberg_id",
            "input_date",
            "target_date"
        ]
    ).to_csv(
        OUT / f"metadata_{split}.csv",
        index=False
    )

    print(
        f"{split.upper():5s}: "
        f"{len(X):,} sequences"
    )

print(f"\nSaved → {OUT}")