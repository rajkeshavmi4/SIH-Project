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

print("\nTEST RESULTS")
print("-" * 30)
print(f"ConvLSTM MAE:  {mae:.6f}")
print(f"ConvLSTM RMSE: {rmse:.6f}")

print("\nBASELINE")
print("-" * 30)
print("Persistence MAE:  0.008508")
print("Persistence RMSE: 0.032685")

print("\nIMPROVEMENT")

mae_improvement = (
    (0.008508 - mae) / 0.008508 * 100
)

rmse_improvement = (
    (0.032685 - rmse) / 0.032685 * 100
)

print(f"MAE improvement:  {mae_improvement:.2f}%")
print(f"RMSE improvement: {rmse_improvement:.2f}%")