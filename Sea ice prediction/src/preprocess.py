from pathlib import Path
import xarray as xr
import numpy as np
from tqdm import tqdm

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

files = list(RAW_DIR.rglob("*S25km*.nc"))

if not files:
    raise FileNotFoundError("No Antarctic S25km files found.")

records = []

for file in tqdm(files, desc="Reading files"):

    try:
        with xr.open_dataset(file) as ds:

            # Automatically find the sea-ice concentration variable
            vars_ = [
                v for v in ds.data_vars
                if v != "crs" and "ICECON" in v.upper()
            ]

            if not vars_:
                print(f"Skipping {file.name}: SIC variable not found")
                continue

            var = vars_[0]
            sic = ds[var].isel(time=0).values.astype(np.float32)
            date = ds["time"].values[0]

            # Keep only valid concentration values
            sic[(sic < 0) | (sic > 1)] = np.nan

            records.append((date, sic))

    except Exception as e:
        print(f"Skipping {file.name}: {e}")


# Sort by ACTUAL date, not filename
records.sort(key=lambda x: x[0])

# Remove duplicate dates
seen = set()
maps = []
dates = []

for date, sic in records:
    date_key = str(np.datetime64(date, "D"))

    if date_key not in seen:
        seen.add(date_key)
        dates.append(np.datetime64(date))
        maps.append(sic)

data = np.stack(maps)
dates = np.array(dates, dtype="datetime64[ns]")

np.save(OUT_DIR / "sic.npy", data)
np.save(OUT_DIR / "dates.npy", dates)

print("\nPREPROCESSING COMPLETE")
print("Files processed:", len(records))
print("Unique dates:", len(dates))
print("Shape:", data.shape)
print("Date range:", dates[0], "to", dates[-1])
print("Valid range:", np.nanmin(data), "to", np.nanmax(data))