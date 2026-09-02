from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt

from model import SeaIceConvLSTM


# ============================================================
# CONFIG
# ============================================================

DATA = "data/processed/test_sic.npy"
DATES = "data/processed/test_dates.npy"
MODEL = "checkpoints/best_model.pt"

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

SIZE = 128
SEQ_LEN = 7


# ============================================================
# LOAD DATA
# ============================================================

print("Loading data...")

raw_data = np.load(DATA).astype(np.float32)
dates = np.load(DATES)

# Original valid-pixel mask
raw_mask = np.isfinite(raw_data).astype(np.float32)

# Replace NaN values
data = np.nan_to_num(
    raw_data,
    nan=0.0
)

# ============================================================
# SAME PREPROCESSING AS TRAINING
# ============================================================

data_tensor = torch.from_numpy(data).unsqueeze(1)

data_tensor = F.interpolate(
    data_tensor,
    size=(SIZE, SIZE),
    mode="bilinear",
    align_corners=False
).squeeze(1)

# Resize validity mask exactly as training
mask_tensor = torch.from_numpy(
    raw_mask
).unsqueeze(1)

mask_tensor = F.interpolate(
    mask_tensor,
    size=(SIZE, SIZE),
    mode="nearest"
).squeeze(1)

print(
    f"Loaded {len(data)} observations"
)

print(
    f"Date range: {dates[0]} → {dates[-1]}"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading model...")

# MUST MATCH TRAINING ARCHITECTURE
model = SeaIceConvLSTM(
    hidden=16
).to(DEVICE)

checkpoint = torch.load(
    MODEL,
    map_location=DEVICE
)

# Your checkpoint contains:
# {"model": ..., "val_loss": ...}

if "model" in checkpoint:

    model.load_state_dict(
        checkpoint["model"]
    )

else:

    model.load_state_dict(
        checkpoint
    )

model.eval()

print("Model loaded successfully.")
print("Using device:", DEVICE)


# ============================================================
# SELECT FORECAST DATE
# ============================================================

print("\n================================")
print("SELECT FORECAST DATE")
print("================================")

date_input = input(
    "Enter forecast date (YYYY-MM-DD): "
).strip()

target_date = np.datetime64(
    date_input
)

matches = np.where(
    dates == target_date
)[0]


if len(matches) == 0:

    raise ValueError(
        f"\nDate {date_input} not found.\n"
        f"Available range: "
        f"{dates[0]} → {dates[-1]}"
    )


target_idx = int(
    matches[0]
)


# ============================================================
# CHECK ENOUGH HISTORY
# ============================================================

if target_idx < SEQ_LEN:

    raise ValueError(
        "\nNot enough previous days "
        "for a 7-day forecast."
    )


# ============================================================
# CHECK PREVIOUS 7 DAYS ARE CONSECUTIVE
# ============================================================

input_dates = dates[
    target_idx - SEQ_LEN:
    target_idx
]

gaps = (
    np.diff(input_dates)
    .astype("timedelta64[D]")
    .astype(int)
)

if not np.all(gaps == 1):

    raise ValueError(
        "\nPrevious 7 observations are "
        "not consecutive days."
    )


# ============================================================
# CREATE INPUT
# ============================================================

# IMPORTANT:
# Selected date is the TARGET.
#
# Example:
#
# Target = 2025-11-01
#
# Input:
# 2025-10-25
# 2025-10-26
# 2025-10-27
# 2025-10-28
# 2025-10-29
# 2025-10-30
# 2025-10-31
#
# Prediction:
# 2025-11-01

x = data_tensor[
    target_idx - SEQ_LEN:
    target_idx
]

x = (
    x
    .unsqueeze(0)
    .unsqueeze(2)
    .to(DEVICE)
)


# ============================================================
# PREDICTION
# ============================================================

print("\nRunning prediction...")

with torch.no_grad():

    prediction = model(x)

prediction = (
    prediction
    .squeeze()
    .cpu()
    .numpy()
)


# ============================================================
# ACTUAL TARGET
# ============================================================

actual = data_tensor[
    target_idx
].numpy()

valid_mask = mask_tensor[
    target_idx
].numpy()


# ============================================================
# ERROR
# ============================================================

error = np.abs(
    prediction - actual
)

# Only evaluate valid pixels
valid_pixels = valid_mask > 0.5

valid_error = error[
    valid_pixels
]

valid_difference = (
    prediction - actual
)[
    valid_pixels
]


# ============================================================
# METRICS
# ============================================================

mae = np.mean(
    np.abs(valid_difference)
)

rmse = np.sqrt(
    np.mean(
        valid_difference ** 2
    )
)


# ============================================================
# RESULTS
# ============================================================

print("\n================================")
print("ANTARCTIC SEA-ICE FORECAST")
print("================================")

print(
    "Input period:"
)

print(
    f"{input_dates[0]} → "
    f"{input_dates[-1]}"
)

print(
    "Forecast date:"
)

print(
    target_date
)

print(
    f"\nValid pixels: "
    f"{valid_pixels.sum():,}"
)

print(
    f"MAE:  {mae:.6f}"
)

print(
    f"RMSE: {rmse:.6f}"
)


# ============================================================
# VISUALIZATION
# ============================================================

fig, ax = plt.subplots(
    1,
    3,
    figsize=(18, 6)
)


# ------------------------------------------------------------
# OBSERVED
# ------------------------------------------------------------

observed_display = np.where(
    valid_pixels,
    actual,
    np.nan
)

im1 = ax[0].imshow(
    observed_display,
    vmin=0,
    vmax=1
)

ax[0].set_title(
    f"Observed SIC\n{date_input}"
)

plt.colorbar(
    im1,
    ax=ax[0],
    fraction=0.046,
    label="Sea-Ice Concentration"
)


# ------------------------------------------------------------
# PREDICTION
# ------------------------------------------------------------

prediction_display = np.where(
    valid_pixels,
    prediction,
    np.nan
)

im2 = ax[1].imshow(
    prediction_display,
    vmin=0,
    vmax=1
)

ax[1].set_title(
    f"AI Predicted SIC\n{date_input}"
)

plt.colorbar(
    im2,
    ax=ax[1],
    fraction=0.046,
    label="Sea-Ice Concentration"
)


# ------------------------------------------------------------
# ERROR
# ------------------------------------------------------------

error_display = np.where(
    valid_pixels,
    error,
    np.nan
)

im3 = ax[2].imshow(
    error_display
)

ax[2].set_title(
    f"Prediction Error\n"
    f"MAE = {mae:.4f}"
)

plt.colorbar(
    im3,
    ax=ax[2],
    fraction=0.046,
    label="Absolute Error"
)


# ============================================================
# AXES
# ============================================================

for a in ax:

    a.set_xlabel(
        "Grid X"
    )

    a.set_ylabel(
        "Grid Y"
    )


# ============================================================
# TITLE
# ============================================================

plt.suptitle(
    "POLARROUTE AI Antarctic Sea-Ice Forecast",
    fontsize=16
)

plt.tight_layout()


# ============================================================
# SAVE
# ============================================================

Path(
    "outputs"
).mkdir(
    exist_ok=True
)

output_file = (
    "outputs/"
    f"sea_ice_prediction_{date_input}.png"
)

plt.savefig(
    output_file,
    dpi=200,
    bbox_inches="tight"
)

print(
    f"\nSaved visualization:"
)

print(
    output_file
)

plt.show()