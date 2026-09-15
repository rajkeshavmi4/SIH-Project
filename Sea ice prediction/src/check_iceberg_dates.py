import pandas as pd
from pathlib import Path

raw_dir = Path("iceberg trajectory/data/raw")
results = []

for f in raw_dir.glob("*.csv"):
    try:
        df = pd.read_csv(f)
        if "date" not in df.columns or len(df) < 7:
            continue
        max_date = df["date"].max()
        results.append((f.name, max_date, len(df)))
    except Exception as e:
        print(f"Skipped {f.name}: {e}")

results.sort(key=lambda x: x[1], reverse=True)

print(f"Total usable files: {len(results)}")
print("\nTop 10 most RECENT icebergs:")
for name, date, rows in results[:10]:
    print(f"{name}: last date={date}, rows={rows}")

print("\nBottom 10 OLDEST icebergs:")
for name, date, rows in results[-10:]:
    print(f"{name}: last date={date}, rows={rows}")