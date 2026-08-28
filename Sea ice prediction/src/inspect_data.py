from pathlib import Path
import xarray as xr

files = sorted(Path("data/raw").rglob("*.nc"))

if not files:
    raise FileNotFoundError("No .nc files found in data/raw")

print(f"Found {len(files)} NetCDF files")
print(f"Inspecting: {files[0]}\n")

ds = xr.open_dataset(files[0])

print(ds)

print("\nDATA VARIABLES:")
for var in ds.data_vars:
    print(f"  {var}: {ds[var].dims} | {ds[var].shape}")

print("\nCOORDINATES:")
print(list(ds.coords))

print("\nDIMENSIONS:")
print(dict(ds.sizes))