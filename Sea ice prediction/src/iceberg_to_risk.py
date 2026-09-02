from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA = Path("data/processed")

PREDICTIONS = Path(
    r"K:\Sih Project\iceberg trajectory\outputs\iceberg\test_predictions.csv"
)

LAT_FILE = DATA / "lat.npy"
LON_FILE = DATA / "lon.npy"

OUTPUT_DIR = Path(
    r"K:\Sih Project\iceberg trajectory\outputs\iceberg"
)

GRID_SIZE = 128

# Risk influence radius in km.
# These are configurable navigation parameters.
RISK_RADIUS_KM = {
    24: 30.0,
    48: 40.0,
    72: 50.0
}

# Relative importance of each forecast horizon.
HORIZON_WEIGHT = {
    24: 1.00,
    48: 0.75,
    72: 0.50
}


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

EARTH_RADIUS_KM = 6371.0088


def haversine_grid(
    lat_grid,
    lon_grid,
    lat,
    lon
):

    lat1 = np.radians(
        lat_grid
    )

    lat2 = np.radians(lat)

    dlat = lat2 - lat1

    dlon = np.radians(
        lon - lon_grid
    )

    a = (
        np.sin(dlat / 2.0) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2.0) ** 2
    )

    return (
        2.0
        * EARTH_RADIUS_KM
        * np.arcsin(
            np.sqrt(a)
        )
    )


# ============================================================
# LOAD
# ============================================================

print("=" * 60)
print("ICEBERG → NAVIGATION RISK")
print("=" * 60)

pred = pd.read_csv(
    PREDICTIONS,
    parse_dates=[
        "input_date",
        "target_date"
    ]
)

lat = np.load(
    LAT_FILE
).astype(np.float32)

lon = np.load(
    LON_FILE
).astype(np.float32)


# ============================================================
# CREATE SAME 128 × 128 GRID
# ============================================================

import torch
import torch.nn.functional as F


lat_tensor = torch.from_numpy(
    lat
).unsqueeze(0).unsqueeze(0)

lon_tensor = torch.from_numpy(
    lon
).unsqueeze(0).unsqueeze(0)

lat_grid = F.interpolate(
    lat_tensor,
    size=(GRID_SIZE, GRID_SIZE),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()

lon_grid = F.interpolate(
    lon_tensor,
    size=(GRID_SIZE, GRID_SIZE),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()


print(
    f"Prediction rows : {len(pred):,}"
)

print(
    f"Navigation grid : {lat_grid.shape}"
)


# ============================================================
# SELECT FORECAST POSITIONS
# ============================================================

# Current prediction file contains 24h predictions.
# The multi-horizon evaluation can be connected later
# if separate 48h and 72h coordinates are exported.

if "predicted_lat" not in pred.columns:

    raise ValueError(
        "predicted_lat column not found."
    )

if "predicted_lon" not in pred.columns:

    raise ValueError(
        "predicted_lon column not found."
    )


# ============================================================
# DETERMINE VALID PREDICTIONS
# ============================================================

pred = pred.dropna(
    subset=[
        "predicted_lat",
        "predicted_lon"
    ]
).copy()

pred = pred[
    pred["predicted_lat"].between(
        -90,
        0
    )
]

pred["predicted_lon"] = (
    (
        pred["predicted_lon"] + 180
    ) % 360
) - 180


print(
    f"Valid predictions: {len(pred):,}"
)


# ============================================================
# INITIALIZE RISK GRID
# ============================================================

risk_grid = np.zeros(
    (GRID_SIZE, GRID_SIZE),
    dtype=np.float32
)

iceberg_count = np.zeros(
    (GRID_SIZE, GRID_SIZE),
    dtype=np.uint16
)


# ============================================================
# CREATE RISK FIELD
# ============================================================

for row in pred.itertuples():

    iceberg_lat = float(
        row.predicted_lat
    )

    iceberg_lon = float(
        row.predicted_lon
    )

    # Current output represents the one-step
    # forecast used by the trained checkpoint.
    horizon = 24

    radius = RISK_RADIUS_KM[
        horizon
    ]

    weight = HORIZON_WEIGHT[
        horizon
    ]

    distance = haversine_grid(
        lat_grid,
        lon_grid,
        iceberg_lat,
        iceberg_lon
    )

    local_risk = np.exp(
        -0.5
        * (distance / radius) ** 2
    )

    local_risk[
        distance > radius * 3
    ] = 0.0

    risk_grid = np.maximum(
        risk_grid,
        (
            local_risk
            * weight
        ).astype(np.float32)
    )

    iceberg_count[
        distance <= radius
    ] += 1


# ============================================================
# NORMALIZE
# ============================================================

risk_grid = np.clip(
    risk_grid,
    0.0,
    1.0
)


# ============================================================
# RISK CLASS
# ============================================================

risk_class = np.zeros(
    risk_grid.shape,
    dtype=np.uint8
)

risk_class[
    (risk_grid >= 0.25)
    & (risk_grid < 0.50)
] = 1

risk_class[
    (risk_grid >= 0.50)
    & (risk_grid < 0.75)
] = 2

risk_class[
    risk_grid >= 0.75
] = 3


# ============================================================
# STATISTICS
# ============================================================

counts = np.bincount(
    risk_class.ravel(),
    minlength=4
)

total = risk_class.size

print("\n" + "=" * 60)
print("ICEBERG RISK DISTRIBUTION")
print("=" * 60)

print(
    f"LOW       : {counts[0]:,} "
    f"({counts[0] / total * 100:.2f}%)"
)

print(
    f"MODERATE  : {counts[1]:,} "
    f"({counts[1] / total * 100:.2f}%)"
)

print(
    f"HIGH      : {counts[2]:,} "
    f"({counts[2] / total * 100:.2f}%)"
)

print(
    f"VERY HIGH : {counts[3]:,} "
    f"({counts[3] / total * 100:.2f}%)"
)

print(
    f"\nMaximum risk : "
    f"{risk_grid.max():.4f}"
)

print(
    f"Mean risk    : "
    f"{risk_grid.mean():.6f}"
)

print(
    f"Cells with iceberg influence : "
    f"{np.sum(iceberg_count > 0):,}"
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

np.savez_compressed(
    OUTPUT_DIR /
    "iceberg_navigation_risk.npz",

    risk=risk_grid,

    risk_class=risk_class,

    iceberg_count=iceberg_count,

    latitude=lat_grid,

    longitude=lon_grid
)


flat = pd.DataFrame(
    {
        "latitude":
            lat_grid.ravel(),

        "longitude":
            lon_grid.ravel(),

        "iceberg_risk":
            risk_grid.ravel(),

        "risk_class":
            risk_class.ravel(),

        "iceberg_count":
            iceberg_count.ravel()
    }
)

flat.to_csv(
    OUTPUT_DIR /
    "iceberg_navigation_risk.csv",
    index=False
)


print("\n" + "=" * 60)
print("FILES SAVED")
print("=" * 60)

print(
    f"→ {OUTPUT_DIR / 'iceberg_navigation_risk.npz'}"
)

print(
    f"→ {OUTPUT_DIR / 'iceberg_navigation_risk.csv'}"
)