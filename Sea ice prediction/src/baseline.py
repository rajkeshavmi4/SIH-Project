import numpy as np

data = np.load("data/processed/test_sic.npy")
dates = np.load("data/processed/test_dates.npy")

mae_sum = 0.0
mse_sum = 0.0
count = 0

for i in range(len(data) - 1):

    gap = (
        dates[i + 1] - dates[i]
    ).astype("timedelta64[D]").astype(int)

    if gap != 1:
        continue

    pred = data[i]
    target = data[i + 1]

    mask = np.isfinite(pred) & np.isfinite(target)

    diff = pred[mask] - target[mask]

    mae_sum += np.abs(diff).sum()
    mse_sum += (diff ** 2).sum()
    count += diff.size

mae = mae_sum / count
rmse = np.sqrt(mse_sum / count)

print(f"Persistence MAE:  {mae:.6f}")
print(f"Persistence RMSE: {rmse:.6f}")
print(f"Valid pixels: {count:,}")