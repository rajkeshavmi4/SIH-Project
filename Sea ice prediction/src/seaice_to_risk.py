from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from model import SeaIceConvLSTM


# ============================================================
# CONFIG
# ============================================================

DATA = Path("data/processed")

SIC_FILE = DATA / "test_sic.npy"
DATES_FILE = DATA / "test_dates.npy"

LAT_FILE = DATA / "lat.npy"
LON_FILE = DATA / "lon.npy"

MODEL_FILE = Path(
    "checkpoints/best_model.pt"
)

OUTPUT_DIR = Path(
    "outputs/seaice"
)

SIZE = 128
SEQ_LEN = 7
HIDDEN = 16

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("SEA-ICE → NAVIGATION RISK")
print("=" * 60)

sic = np.load(
    SIC_FILE
).astype(np.float32)

dates = np.load(
    DATES_FILE
)

lat = np.load(
    LAT_FILE
).astype(np.float32)

lon = np.load(
    LON_FILE
).astype(np.float32)

print(
    f"SIC shape : {sic.shape}"
)

print(
    f"Lat shape : {lat.shape}"
)

print(
    f"Lon shape : {lon.shape}"
)

print(
    f"Device    : {DEVICE}"
)


# ============================================================
# CLEAN SIC
# ============================================================

sic = np.nan_to_num(
    sic,
    nan=0.0,
    posinf=0.0,
    neginf=0.0
)

sic = np.clip(
    sic,
    0.0,
    1.0
)


# ============================================================
# RESIZE SIC
# EXACTLY AS TRAINING
# ============================================================

sic_tensor = torch.from_numpy(
    sic
).unsqueeze(1)

sic_resized = F.interpolate(
    sic_tensor,
    size=(SIZE, SIZE),
    mode="bilinear",
    align_corners=False
).squeeze(1)


# ============================================================
# RESIZE GEOGRAPHIC GRID
# ============================================================

lat_tensor = torch.from_numpy(
    lat
).unsqueeze(0).unsqueeze(0)

lon_tensor = torch.from_numpy(
    lon
).unsqueeze(0).unsqueeze(0)

lat_resized = F.interpolate(
    lat_tensor,
    size=(SIZE, SIZE),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()

lon_resized = F.interpolate(
    lon_tensor,
    size=(SIZE, SIZE),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()


print(
    f"Navigation grid: {lat_resized.shape}"
)

print(
    f"Latitude range : "
    f"{lat_resized.min():.2f} → "
    f"{lat_resized.max():.2f}"
)

print(
    f"Longitude range: "
    f"{lon_resized.min():.2f} → "
    f"{lon_resized.max():.2f}"
)


# ============================================================
# LOAD MODEL
# ============================================================

model = SeaIceConvLSTM(
    hidden=HIDDEN
).to(DEVICE)

checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
    weights_only=False
)

if isinstance(checkpoint, dict) and "model" in checkpoint:

    model.load_state_dict(
        checkpoint["model"]
    )

else:

    model.load_state_dict(
        checkpoint
    )

model.eval()


# ============================================================
# DATE SELECTION
# ============================================================

print("\nAvailable test period:")

print(
    dates[0],
    "→",
    dates[-1]
)

date_input = input(
    "\nEnter forecast start date "
    "(YYYY-MM-DD): "
).strip()

target_date = np.datetime64(
    date_input,
    "D"
)

date_days = dates.astype(
    "datetime64[D]"
)

matches = np.where(
    date_days == target_date
)[0]

if len(matches) == 0:

    raise ValueError(
        f"Date {date_input} not found "
        "in test dataset."
    )

idx = int(matches[0])


# ============================================================
# CHECK HISTORY
# ============================================================

if idx < SEQ_LEN - 1:

    raise ValueError(
        "Not enough previous observations "
        "for a 7-day sequence."
    )

if idx >= len(sic_resized) - 1:

    raise ValueError(
        "Selected date has no next-day "
        "sea-ice observation."
    )


# ============================================================
# BUILD INPUT SEQUENCE
# ============================================================

x = sic_resized[
    idx - SEQ_LEN + 1:
    idx + 1
]

x = x.unsqueeze(1)
x = x.unsqueeze(0)
x = x.to(DEVICE)


print(
    "\nInput sequence:"
)

print(
    dates[
        idx - SEQ_LEN + 1
    ],
    "→",
    dates[idx]
)


# ============================================================
# FORECAST
# ============================================================

with torch.no_grad():

    prediction = model(x)

prediction = (
    prediction
    .squeeze()
    .cpu()
    .numpy()
)

prediction = np.nan_to_num(
    prediction,
    nan=0.0,
    posinf=0.0,
    neginf=0.0
)

prediction = np.clip(
    prediction,
    0.0,
    1.0
)


forecast_date = (
    dates[idx]
    + np.timedelta64(1, "D")
)


# ============================================================
# SEA-ICE RISK
# ============================================================
#
# Continuous risk:
#
# 0 = open water
# 1 = maximum SIC
#
# This is deliberately kept continuous
# for the route optimizer.
# ============================================================

seaice_risk = prediction.copy()


# ============================================================
# RISK CLASSIFICATION
# ============================================================

risk_class = np.zeros_like(
    seaice_risk,
    dtype=np.uint8
)

risk_class[
    (seaice_risk >= 0.15)
    & (seaice_risk < 0.40)
] = 1

risk_class[
    (seaice_risk >= 0.40)
    & (seaice_risk < 0.70)
] = 2

risk_class[
    seaice_risk >= 0.70
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
print("SEA-ICE FORECAST")
print("=" * 60)

print(
    f"Forecast date : "
    f"{forecast_date}"
)

print(
    f"SIC min       : "
    f"{prediction.min():.4f}"
)

print(
    f"SIC max       : "
    f"{prediction.max():.4f}"
)

print(
    f"SIC mean      : "
    f"{prediction.mean():.4f}"
)

print(
    "\nRISK DISTRIBUTION"
)

print(
    f"LOW       : "
    f"{counts[0]:,} "
    f"({counts[0] / total * 100:.2f}%)"
)

print(
    f"MODERATE  : "
    f"{counts[1]:,} "
    f"({counts[1] / total * 100:.2f}%)"
)

print(
    f"HIGH      : "
    f"{counts[2]:,} "
    f"({counts[2] / total * 100:.2f}%)"
)

print(
    f"VERY HIGH : "
    f"{counts[3]:,} "
    f"({counts[3] / total * 100:.2f}%)"
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
    "seaice_navigation_risk.npz",
    sic=prediction,
    risk=seaice_risk,
    risk_class=risk_class,
    latitude=lat_resized,
    longitude=lon_resized,
    forecast_date=str(forecast_date),
    input_start=str(
        dates[idx - SEQ_LEN + 1]
    ),
    input_end=str(
        dates[idx]
    )
)

# Flattened CSV for inspection

flat = pd.DataFrame(
    {
        "latitude":
            lat_resized.ravel(),

        "longitude":
            lon_resized.ravel(),

        "sic":
            prediction.ravel(),

        "risk":
            seaice_risk.ravel(),

        "risk_class":
            risk_class.ravel()
    }
)

flat.to_csv(
    OUTPUT_DIR /
    "seaice_navigation_risk.csv",
    index=False
)
print(
    f"Model input shape: {x.shape}"
)

print("\n" + "=" * 60)

print(
    "FILES SAVED"
)

print(
    f"→ {OUTPUT_DIR / 'seaice_navigation_risk.npz'}"
)

print(
    f"→ {OUTPUT_DIR / 'seaice_navigation_risk.csv'}"
)

print("=" * 60)