from pathlib import Path

import numpy as np
import pandas as pd
import torch

from iceberg_model import IcebergGRU


# ============================================================
# CONFIG
# ============================================================

DATA = Path("data/processed/iceberg_ml")
MODEL = Path("checkpoints/iceberg_gru_best.pt")
OUTPUT = Path("outputs/iceberg")

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

BATCH_SIZE = 1024


# ============================================================
# HAVERSINE
# ============================================================

EARTH_RADIUS_KM = 6371.0088


def haversine(lat1, lon1, lat2, lon2):

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)

    dlat = lat2 - lat1
    dlon = np.radians(lon2 - lon1)

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * np.arcsin(np.sqrt(a))
    )


# ============================================================
# LOAD TEST DATA
# ============================================================

X = np.load(
    DATA / "X_test.npy"
).astype(np.float32)

Y = np.load(
    DATA / "Y_1d_test.npy"
).astype(np.float32)

metadata = pd.read_csv(
    DATA / "metadata_test.csv",
    parse_dates=[
        "input_date",
        "target_date"
    ]
)

print("=" * 60)
print("ICEBERG GRU TEST EVALUATION")
print("=" * 60)

print(f"Test sequences : {len(X):,}")
print(f"Device         : {DEVICE}")


# ============================================================
# LOAD CHECKPOINT
# ============================================================

checkpoint = torch.load(
    MODEL,
    map_location=DEVICE,
    weights_only=False
)

model = IcebergGRU().to(DEVICE)

model.load_state_dict(
    checkpoint["model"]
)

model.eval()

mean = np.asarray(
    checkpoint["mean"],
    dtype=np.float32
)

std = np.asarray(
    checkpoint["std"],
    dtype=np.float32
)

X_norm = (
    X - mean
) / std


# ============================================================
# PREDICT
# ============================================================

predictions = []

with torch.no_grad():

    for start in range(
        0,
        len(X_norm),
        BATCH_SIZE
    ):

        batch = torch.from_numpy(
            X_norm[
                start:start + BATCH_SIZE
            ]
        ).to(DEVICE)

        pred = model(batch)

        predictions.append(
            pred.cpu().numpy()
        )

predictions = np.concatenate(
    predictions,
    axis=0
)


# ============================================================
# RECONSTRUCT POSITIONS
# ============================================================

current_lat = X[:, -1, 0]
current_lon = X[:, -1, 1]

actual_lat = (
    current_lat + Y[:, 0]
)

actual_lon = (
    current_lon + Y[:, 1]
)

pred_lat = (
    current_lat + predictions[:, 0]
)

pred_lon = (
    current_lon + predictions[:, 1]
)


# ============================================================
# PERSISTENCE BASELINE
# ============================================================

persistence_lat = current_lat
persistence_lon = current_lon


# ============================================================
# ERROR
# ============================================================

gru_error = haversine(
    actual_lat,
    actual_lon,
    pred_lat,
    pred_lon
)

persistence_error = haversine(
    actual_lat,
    actual_lon,
    persistence_lat,
    persistence_lon
)


# ============================================================
# METRICS
# ============================================================

gru_mae = np.mean(
    np.abs(gru_error)
)

gru_rmse = np.sqrt(
    np.mean(gru_error ** 2)
)

gru_median = np.median(
    gru_error
)

persistence_mae = np.mean(
    np.abs(persistence_error)
)

persistence_rmse = np.sqrt(
    np.mean(persistence_error ** 2)
)

persistence_median = np.median(
    persistence_error
)

improvement = (
    (persistence_mae - gru_mae)
    / persistence_mae
    * 100
)


# ============================================================
# ADE / FDE
# ============================================================

ADE = np.mean(
    gru_error
)

FDE = np.median(
    gru_error
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 60)
print("PERSISTENCE BASELINE")
print("=" * 60)

print(
    f"MAE     : {persistence_mae:.3f} km"
)

print(
    f"RMSE    : {persistence_rmse:.3f} km"
)

print(
    f"Median  : {persistence_median:.3f} km"
)


print("\n" + "=" * 60)
print("GRU MODEL")
print("=" * 60)

print(
    f"MAE     : {gru_mae:.3f} km"
)

print(
    f"RMSE    : {gru_rmse:.3f} km"
)

print(
    f"Median  : {gru_median:.3f} km"
)


print("\n" + "=" * 60)
print("IMPROVEMENT")
print("=" * 60)

print(
    f"MAE improvement : {improvement:.2f}%"
)

print(
    f"ADE             : {ADE:.3f} km"
)

print(
    f"FDE             : {FDE:.3f} km"
)


# ============================================================
# ERROR DISTRIBUTION
# ============================================================

print("\n" + "=" * 60)
print("ERROR PERCENTILES")
print("=" * 60)

for p in [
    50,
    75,
    90,
    95,
    99
]:

    print(
        f"P{p:02d} GRU error : "
        f"{np.percentile(gru_error, p):.3f} km"
    )


# ============================================================
# SAVE PREDICTIONS
# ============================================================

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)

results = metadata.copy()

results["current_lat"] = current_lat
results["current_lon"] = current_lon

results["actual_lat"] = actual_lat
results["actual_lon"] = actual_lon

results["predicted_lat"] = pred_lat
results["predicted_lon"] = pred_lon

results["gru_error_km"] = gru_error
results["persistence_error_km"] = persistence_error

results.to_csv(
    OUTPUT / "test_predictions.csv",
    index=False
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    {
        "metric": [
            "test_sequences",
            "persistence_mae_km",
            "persistence_rmse_km",
            "persistence_median_km",
            "gru_mae_km",
            "gru_rmse_km",
            "gru_median_km",
            "mae_improvement_percent",
            "ADE_km",
            "FDE_km"
        ],
        "value": [
            len(X),
            persistence_mae,
            persistence_rmse,
            persistence_median,
            gru_mae,
            gru_rmse,
            gru_median,
            improvement,
            ADE,
            FDE
        ]
    }
)

summary.to_csv(
    OUTPUT / "evaluation_summary.csv",
    index=False
)

print(
    f"\nSaved → "
    f"{OUTPUT / 'test_predictions.csv'}"
)

print(
    f"Saved → "
    f"{OUTPUT / 'evaluation_summary.csv'}"
)