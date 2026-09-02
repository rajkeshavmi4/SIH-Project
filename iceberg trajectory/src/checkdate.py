from pathlib import Path
import pandas as pd

RAW = Path("data/iceberg/raw")

for file in RAW.glob("*.csv"):
    df = pd.read_csv(file)

    if "date" not in df.columns:
        continue

    dates = pd.to_datetime(
        df["date"].astype(str).str.strip(),
        format="%Y%j",
        errors="coerce"
    )

    years = dates.dt.year.dropna()

    if len(years) and (years.min() < 1970 or years.max() > 2026):
        print("\nFILE:", file.name)
        print("Raw first:", df["date"].iloc[0])
        print("Raw last :", df["date"].iloc[-1])
        print("Parsed   :", dates.iloc[0], "→", dates.iloc[-1])
        print("Min year :", years.min())
        print("Max year :", years.max())