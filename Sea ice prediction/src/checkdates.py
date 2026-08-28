import numpy as np

dates = np.load("data/processed/dates.npy")

diffs = np.diff(dates).astype("timedelta64[D]").astype(int)

print("Total samples:", len(dates))
print("Date range:", dates[0], "to", dates[-1])
print("Unique day gaps:", np.unique(diffs))

missing = np.where(diffs != 1)[0]

print("Gaps found:", len(missing))

for i in missing[:20]:
    print(
        dates[i],
        "→",
        dates[i + 1],
        f"({diffs[i]} days)"
    )