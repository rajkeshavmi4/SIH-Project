from pathlib import Path
import numpy as np

ROOT = Path("data/processed")

print("=" * 60)
print("SEA-ICE GRID INSPECTION")
print("=" * 60)

for path in sorted(ROOT.rglob("*.npy")):

    try:
        arr = np.load(path, allow_pickle=False)

        print(
            f"\n{path}"
            f"\n  shape : {arr.shape}"
            f"\n  dtype : {arr.dtype}"
        )

        if np.issubdtype(arr.dtype, np.number):

            finite = arr[np.isfinite(arr)]

            if len(finite):
                print(
                    f"  min   : {finite.min():.6f}"
                )
                print(
                    f"  max   : {finite.max():.6f}"
                )

    except Exception as e:

        print(
            f"\n{path}"
            f"\n  ERROR: {e}"
        )

print("\n" + "=" * 60)
print("LOOKING FOR LAT/LON FILES")
print("=" * 60)

keywords = [
    "lat",
    "latitude",
    "lon",
    "longitude",
    "grid",
    "coord"
]

for path in ROOT.rglob("*"):

    if path.is_file():

        name = path.name.lower()

        if any(k in name for k in keywords):

            print(path)