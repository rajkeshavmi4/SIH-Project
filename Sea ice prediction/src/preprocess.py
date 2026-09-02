from pathlib import Path

import numpy as np
import xarray as xr
from pyproj import Transformer
from tqdm import tqdm

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

files = list(RAW_DIR.rglob("*S25km*.nc"))

if not files:
    raise FileNotFoundError("No Antarctic S25km files found.")

records = []
geo_x = None
geo_y = None

for file in tqdm(files, desc="Reading files"):
    try:
        with xr.open_dataset(file) as ds:
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

            sic[(sic < 0) | (sic > 1)] = np.nan

            if geo_x is None or geo_y is None:
                geo_x = np.asarray(ds["x"].values, dtype=np.float64)
                geo_y = np.asarray(ds["y"].values, dtype=np.float64)

            records.append((date, sic))
    except Exception as e:
        print(f"Skipping {file.name}: {e}")

records.sort(key=lambda x: x[0])

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

transformer = Transformer.from_crs("EPSG:3412", "EPSG:4326", always_xy=True)
xx, yy = np.meshgrid(geo_x, geo_y)
lon, lat = transformer.transform(xx, yy)

np.save(OUT_DIR / "sic.npy", data)
np.save(OUT_DIR / "dates.npy", dates)
np.save(OUT_DIR / "x.npy", geo_x)
np.save(OUT_DIR / "y.npy", geo_y)
np.save(OUT_DIR / "lat.npy", lat.astype(np.float32))
np.save(OUT_DIR / "lon.npy", lon.astype(np.float32))

print("\nPREPROCESSING COMPLETE")
print("Files processed:", len(records))
print("Unique dates:", len(dates))
print("Shape:", data.shape)
print("Date range:", dates[0], "to", dates[-1])
print("Valid range:", np.nanmin(data), "to", np.nanmax(data))
print("Lat/Lon grid shape:", lat.shape)
print("Lat bounds:", float(np.nanmin(lat)), "to", float(np.nanmax(lat)))
print("Lon bounds:", float(np.nanmin(lon)), "to", float(np.nanmax(lon)))