from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

SEAICE = Path(
    r"K:\Sih Project\Sea ice prediction"
)

ICEBERG = Path(
    r"K:\Sih Project\iceberg trajectory"
)

SEAICE_FILE = (
    SEAICE
    / "outputs"
    / "seaice"
    / "seaice_navigation_risk.npz"
)

ICEBERG_FILE = (
    ICEBERG
    / "outputs"
    / "iceberg"
    / "iceberg_navigation_risk.npz"
)

OUTPUT_DIR = (
    SEAICE
    / "outputs"
    / "navigation"
)


# ============================================================
# WEIGHTS
# ============================================================

SEAICE_WEIGHT = 0.60
ICEBERG_WEIGHT = 0.40


# ============================================================
# LOAD
# ============================================================

print("=" * 60)
print("COMPOSITE NAVIGATION RISK")
print("=" * 60)

seaice = np.load(
    SEAICE_FILE
)

iceberg = np.load(
    ICEBERG_FILE
)

seaice_risk = seaice["risk"].astype(
    np.float32
)

iceberg_risk = iceberg["risk"].astype(
    np.float32
)

lat = seaice["latitude"].astype(
    np.float32
)

lon = seaice["longitude"].astype(
    np.float32
)


# ============================================================
# VALIDATION
# ============================================================

print(
    f"Sea-ice grid : {seaice_risk.shape}"
)

print(
    f"Iceberg grid : {iceberg_risk.shape}"
)

if seaice_risk.shape != iceberg_risk.shape:

    raise ValueError(
        "Sea-ice and iceberg grids do not match."
    )

if lat.shape != seaice_risk.shape:

    raise ValueError(
        "Latitude grid does not match risk grid."
    )

if lon.shape != seaice_risk.shape:

    raise ValueError(
        "Longitude grid does not match risk grid."
    )


# ============================================================
# COMBINE
# ============================================================

composite_risk = (
    SEAICE_WEIGHT * seaice_risk
    +
    ICEBERG_WEIGHT * iceberg_risk
)


composite_risk = np.clip(
    composite_risk,
    0.0,
    1.0
)


# ============================================================
# RISK CLASSIFICATION
# ============================================================

risk_class = np.zeros_like(
    composite_risk,
    dtype=np.uint8
)

risk_class[
    (composite_risk >= 0.25)
    &
    (composite_risk < 0.50)
] = 1

risk_class[
    (composite_risk >= 0.50)
    &
    (composite_risk < 0.75)
] = 2

risk_class[
    composite_risk >= 0.75
] = 3


# ============================================================
# STATISTICS
# ============================================================

counts = np.bincount(
    risk_class.ravel(),
    minlength=4
)

total = composite_risk.size

print("\nRisk distribution:")

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
    f"\nMean composite risk : "
    f"{composite_risk.mean():.4f}"
)

print(
    f"Maximum risk        : "
    f"{composite_risk.max():.4f}"
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

np.savez_compressed(
    OUTPUT_DIR / "composite_navigation_risk.npz",
    risk=composite_risk,
    risk_class=risk_class,
    seaice_risk=seaice_risk,
    iceberg_risk=iceberg_risk,
    latitude=lat,
    longitude=lon,
    seaice_weight=SEAICE_WEIGHT,
    iceberg_weight=ICEBERG_WEIGHT
)


flat = pd.DataFrame(
    {
        "latitude": lat.ravel(),
        "longitude": lon.ravel(),
        "seaice_risk": seaice_risk.ravel(),
        "iceberg_risk": iceberg_risk.ravel(),
        "composite_risk": composite_risk.ravel(),
        "risk_class": risk_class.ravel()
    }
)

flat.to_csv(
    OUTPUT_DIR / "composite_navigation_risk.csv",
    index=False
)


print("\n" + "=" * 60)
print("FILES SAVED")
print("=" * 60)

print(
    OUTPUT_DIR
    / "composite_navigation_risk.npz"
)

print(
    OUTPUT_DIR
    / "composite_navigation_risk.csv"
)