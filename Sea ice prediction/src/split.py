import numpy as np

data = np.load("data/processed/sic.npy")
dates = np.load("data/processed/dates.npy")

n = len(data)

train_end = int(n * 0.70)
val_end = int(n * 0.85)

splits = {
    "train": slice(0, train_end),
    "val": slice(train_end, val_end),
    "test": slice(val_end, n)
}

for name, s in splits.items():
    x = data[s]
    d = dates[s]

    np.save(f"data/processed/{name}_sic.npy", x)
    np.save(f"data/processed/{name}_dates.npy", d)

    print(
        f"{name.upper():5} | "
        f"{len(x):4} samples | "
        f"{d[0]} → {d[-1]}"
    )