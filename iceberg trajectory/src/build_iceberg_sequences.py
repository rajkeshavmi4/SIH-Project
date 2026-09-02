from pathlib import Path
import numpy as np
import pandas as pd

INPUT = Path("data/processed/trajectory_features.csv")
OUT = Path("data/processed/iceberg_ml")

SEQ_LEN = 7
HORIZONS = [1, 2, 3]
SEED = 42

FEATURES = [
    "latitude",
    "longitude",
    "delta_lat",
    "delta_lon",
    "speed_kmh"
]

rng = np.random.default_rng(SEED)

df = pd.read_csv(INPUT, parse_dates=["date"])
df = df.sort_values(["track_id", "date"]).reset_index(drop=True)

tracks = []

for track_id, g in df.groupby("track_id", sort=False):
    g = g.dropna(subset=FEATURES).reset_index(drop=True)

    if len(g) < SEQ_LEN + max(HORIZONS):
        continue

    tracks.append(track_id)

tracks = np.array(tracks)
rng.shuffle(tracks)

n = len(tracks)
n_train = int(n * 0.70)
n_val = int(n * 0.15)

train_tracks = set(tracks[:n_train])
val_tracks = set(tracks[n_train:n_train + n_val])
test_tracks = set(tracks[n_train + n_val:])

print(f"Tracks: {n}")
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

        for i in range(SEQ_LEN, len(g) - max(HORIZONS)):

            x = values[i - SEQ_LEN:i]

            X.append(x)

            for h in HORIZONS:
                future = latlon[i + h - 1]
                current = latlon[i - 1]
                Y[h].append(future - current)

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