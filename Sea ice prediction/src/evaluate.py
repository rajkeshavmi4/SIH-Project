import numpy as np
import torch
from torch.utils.data import DataLoader

from dataset import SeaIceDataset
from model import SeaIceConvLSTM


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

test_ds = SeaIceDataset(
    "data/processed/test_sic.npy",
    "data/processed/test_dates.npy",
    seq_len=7
)

loader = DataLoader(
    test_ds,
    batch_size=2,
    shuffle=False
)

model = SeaIceConvLSTM(hidden=16).to(DEVICE)

checkpoint = torch.load(
    "checkpoints/best_model.pt",
    map_location=DEVICE
)

model.load_state_dict(checkpoint["model"])
model.eval()

abs_error = 0.0
sq_error = 0.0
pixels = 0
baseline_abs_error = 0.0
baseline_sq_error = 0.0
baseline_pixels = 0

for index in test_ds.indices:
    previous = np.asarray(test_ds.data[index + 6], dtype=np.float32)
    target = np.asarray(test_ds.data[index + 7], dtype=np.float32)
    valid = np.isfinite(previous) & np.isfinite(target)
    difference = previous[valid] - target[valid]

    baseline_abs_error += np.abs(difference).sum()
    baseline_sq_error += (difference ** 2).sum()
    baseline_pixels += difference.size

with torch.no_grad():

    for x, y, mask in loader:

        x = x.to(DEVICE)
        y = y.to(DEVICE)
        mask = mask.to(DEVICE)

        pred = model(x)

        diff = (pred - y) * mask

        abs_error += diff.abs().sum().item()
        sq_error += (diff ** 2).sum().item()
        pixels += mask.sum().item()


mae = abs_error / pixels
rmse = (sq_error / pixels) ** 0.5
baseline_mae = baseline_abs_error / baseline_pixels
baseline_rmse = (baseline_sq_error / baseline_pixels) ** 0.5

print("\nTEST RESULTS")
print("-" * 30)
print(f"ConvLSTM MAE:  {mae:.6f}")
print(f"ConvLSTM RMSE: {rmse:.6f}")

print("\nBASELINE")
print("-" * 30)
print(f"Persistence MAE:  {baseline_mae:.6f}")
print(f"Persistence RMSE: {baseline_rmse:.6f}")

print("\nIMPROVEMENT")

mae_improvement = (
    (baseline_mae - mae) / baseline_mae * 100
)

rmse_improvement = (
    (baseline_rmse - rmse) / baseline_rmse * 100
)

print(f"MAE change vs persistence:  {mae_improvement:+.2f}%")
print(f"RMSE change vs persistence: {rmse_improvement:+.2f}%")