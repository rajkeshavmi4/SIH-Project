from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

SIC_FILE = (
    ROOT
    / "data"
    / "processed"
    / "test_sic.npy"
)

LAT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "lat.npy"
)

LON_FILE = (
    ROOT
    / "data"
    / "processed"
    / "lon.npy"
)

RISK_FILE = (
    ROOT
    / "outputs"
    / "navigation"
    / "composite_navigation_risk.npz"
)

OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "navigation"
)


GRID_SIZE = 128


# ============================================================
# LOAD
# ============================================================

print("=" * 65)
print("POLARROUTE AI")
print("NAVIGATION MASK BUILDER")
print("=" * 65)

sic = np.load(
    SIC_FILE
)

lat = np.load(
    LAT_FILE
).astype(
    np.float32
)

lon = np.load(
    LON_FILE
).astype(
    np.float32
)

risk_data = np.load(
    RISK_FILE
)

risk = risk_data[
    "risk"
].astype(
    np.float32
)


print(
    f"\nSIC shape : {sic.shape}"
)

print(
    f"Lat shape : {lat.shape}"
)

print(
    f"Lon shape : {lon.shape}"
)


# ============================================================
# VALIDATE
# ============================================================

if sic.ndim != 3:

    raise ValueError(
        "SIC must have shape "
        "(time, latitude, longitude)."
    )

if lat.shape != sic.shape[1:]:

    raise ValueError(
        "Latitude grid does not match SIC."
    )

if lon.shape != sic.shape[1:]:

    raise ValueError(
        "Longitude grid does not match SIC."
    )


# ============================================================
# ORIGINAL VALID DATA MASK
# ============================================================

finite = np.isfinite(
    sic
)

valid_fraction = finite.mean(
    axis=0
)

nan_fraction = 1.0 - valid_fraction


print("\nOriginal coverage:")

print(
    f"Valid cells : "
    f"{np.sum(valid_fraction > 0):,}"
)

print(
    f"Always invalid cells : "
    f"{np.sum(valid_fraction == 0):,}"
)


# ============================================================
# LAND / INVALID MASK
# ============================================================

# Cells without observations throughout the test period
# are treated as non-navigable.

land_mask = (
    valid_fraction == 0
)


# ============================================================
# RESIZE TO NAVIGATION GRID
# ============================================================

land_tensor = torch.from_numpy(
    land_mask.astype(
        np.float32
    )
).unsqueeze(
    0
).unsqueeze(
    0
)

valid_tensor = torch.from_numpy(
    (
        ~land_mask
    ).astype(
        np.float32
    )
).unsqueeze(
    0
).unsqueeze(
    0
)


land_128 = F.interpolate(
    land_tensor,
    size=(
        GRID_SIZE,
        GRID_SIZE
    ),
    mode="nearest"
).squeeze().numpy().astype(
    bool
)

valid_128 = F.interpolate(
    valid_tensor,
    size=(
        GRID_SIZE,
        GRID_SIZE
    ),
    mode="nearest"
).squeeze().numpy().astype(
    bool
)


# ============================================================
# FINAL NAVIGABLE MASK
# ============================================================

navigable = (
    valid_128
    &
    ~land_128
)


print("\nNavigation grid:")

print(
    f"Navigable cells : "
    f"{navigable.sum():,}"
)

print(
    f"Blocked cells   : "
    f"{(~navigable).sum():,}"
)

print(
    f"Navigable area  : "
    f"{navigable.mean() * 100:.2f}%"
)


# ============================================================
# COORDINATE GRID
# ============================================================

lat_tensor = torch.from_numpy(
    lat
).unsqueeze(
    0
).unsqueeze(
    0
)

lon_tensor = torch.from_numpy(
    lon
).unsqueeze(
    0
).unsqueeze(
    0
)

lat_128 = F.interpolate(
    lat_tensor,
    size=(
        GRID_SIZE,
        GRID_SIZE
    ),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()

lon_128 = F.interpolate(
    lon_tensor,
    size=(
        GRID_SIZE,
        GRID_SIZE
    ),
    mode="bilinear",
    align_corners=False
).squeeze().numpy()


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

output = (
    OUTPUT_DIR
    / "navigation_mask.npz"
)

np.savez_compressed(
    output,
    navigable=navigable,
    land_mask=land_128,
    latitude=lat_128,
    longitude=lon_128
)


print("\n" + "=" * 65)
print("NAVIGATION MASK SAVED")
print("=" * 65)

print(
    output
)