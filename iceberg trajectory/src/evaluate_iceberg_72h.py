from pathlib import Path

import numpy as np
import pandas as pd
import torch

from iceberg_model import IcebergGRU


DATA = Path(
    "data/processed/iceberg_ml"
)

MODEL = Path(
    "checkpoints/iceberg_gru_72h_best.pt"
)

OUTPUT = Path(
    "outputs/iceberg"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

BATCH_SIZE = 1024

EARTH_RADIUS_KM = 6371.0088


def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)

    dlat = lat2 - lat1

    dlon = np.radians(
        lon2 - lon1
    )

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * np.arcsin(
            np.sqrt(a)
        )
    )


# ============================================================
# LOAD TEST DATA
# ============================================================

X = np.load(
    DATA / "X_test.npy"
).astype(np.float32)

Y = np.stack(
    [
        np.load(DATA / "Y_1d_test.npy"),
        np.load(DATA / "Y_2d_test.npy"),
        np.load(DATA / "Y_3d_test.npy")
    ],
    axis=1
).astype(np.float32)

metadata = pd.read_csv(
    DATA / "metadata_test.csv",
    parse_dates=[
        "input_date",
        "target_date"
    ]
)


print("=" * 60)
print("ICEBERG 72-HOUR TEST EVALUATION")
print("=" * 60)

print(
    f"Test sequences : {len(X):,}"
)

print(
    f"Device         : {DEVICE}"
)


# ============================================================
# LOAD MODEL
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
                start:
                start + BATCH_SIZE
            ]
        ).to(DEVICE)

        pred = model(
            batch
        )

        predictions.append(
            pred.cpu().numpy()
        )

predictions = np.concatenate(
    predictions,
    axis=0
)


# ============================================================
# EVALUATE EACH HORIZON
# ============================================================

all_results = []

current_lat = X[:, -1, 0]
current_lon = X[:, -1, 1]

for h_idx, hours in enumerate(
    [24, 48, 72]
):

    actual_lat = (
        current_lat
        + Y[:, h_idx, 0]
    )

    actual_lon = (
        current_lon
        + Y[:, h_idx, 1]
    )

    pred_lat = (
        current_lat
        + predictions[:, h_idx, 0]
    )

    pred_lon = (
        current_lon
        + predictions[:, h_idx, 1]
    )

    persistence_error = haversine(
        actual_lat,
        actual_lon,
        current_lat,
        current_lon
    )

    gru_error = haversine(
        actual_lat,
        actual_lon,
        pred_lat,
        pred_lon
    )

    persistence_mae = np.mean(
        persistence_error
    )

    persistence_rmse = np.sqrt(
        np.mean(
            persistence_error ** 2
        )
    )

    persistence_median = np.median(
        persistence_error
    )

    gru_mae = np.mean(
        gru_error
    )

    gru_rmse = np.sqrt(
        np.mean(
            gru_error ** 2
        )
    )

    gru_median = np.median(
        gru_error
    )

    improvement = (
        (
            persistence_mae
            - gru_mae
        )
        / persistence_mae
        * 100
    )

    print(
        "\n" + "-" * 60
    )

    print(
        f"{hours}-HOUR FORECAST"
    )

    print(
        "-" * 60
    )

    print(
        f"Persistence MAE    : "
        f"{persistence_mae:.3f} km"
    )

    print(
        f"Persistence RMSE   : "
        f"{persistence_rmse:.3f} km"
    )

    print(
        f"Persistence Median : "
        f"{persistence_median:.3f} km"
    )

    print()

    print(
        f"GRU MAE            : "
        f"{gru_mae:.3f} km"
    )

    print(
        f"GRU RMSE           : "
        f"{gru_rmse:.3f} km"
    )

    print(
        f"GRU Median         : "
        f"{gru_median:.3f} km"
    )

    print()

    print(
        f"MAE improvement    : "
        f"{improvement:.2f}%"
    )

    all_results.append(
        {
            "horizon_hours": hours,
            "persistence_mae_km":
                persistence_mae,
            "persistence_rmse_km":
                persistence_rmse,
            "persistence_median_km":
                persistence_median,
            "gru_mae_km":
                gru_mae,
            "gru_rmse_km":
                gru_rmse,
            "gru_median_km":
                gru_median,
            "improvement_percent":
                improvement
        }
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)

results = pd.DataFrame(
    all_results
)

results.to_csv(
    OUTPUT /
    "72h_evaluation.csv",
    index=False
)

print(
    "\n" + "=" * 60
)

print(
    f"Saved → "
    f"{OUTPUT / '72h_evaluation.csv'}"
)