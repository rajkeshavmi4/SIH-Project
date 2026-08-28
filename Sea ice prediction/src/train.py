from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import SeaIceDataset
from model import SeaIceConvLSTM


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

EPOCHS = 20
BATCH_SIZE = 2
LR = 1e-3
SEQ_LEN = 7

Path("checkpoints").mkdir(exist_ok=True)


def masked_mse(pred, target, mask):
    diff = (pred - target) ** 2
    return (diff * mask).sum() / mask.sum().clamp_min(1)


train_ds = SeaIceDataset(
    "data/processed/train_sic.npy",
    "data/processed/train_dates.npy",
    SEQ_LEN
)

val_ds = SeaIceDataset(
    "data/processed/val_sic.npy",
    "data/processed/val_dates.npy",
    SEQ_LEN
)

train_loader = DataLoader(
    train_ds,
    batch_size=BATCH_SIZE,
    shuffle=True,
    pin_memory=(DEVICE == "cuda")
)

val_loader = DataLoader(
    val_ds,
    batch_size=BATCH_SIZE,
    shuffle=False,
    pin_memory=(DEVICE == "cuda")
)

model = SeaIceConvLSTM(hidden=16).to(DEVICE)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=1e-5
)

scaler = torch.amp.GradScaler(
    "cuda",
    enabled=(DEVICE == "cuda")
)

best_val = float("inf")

print(f"\nUsing device: {DEVICE}")

for epoch in range(EPOCHS):

    model.train()
    train_loss = 0.0

    for x, y, mask in train_loader:

        x = x.to(DEVICE, non_blocking=True)
        y = y.to(DEVICE, non_blocking=True)
        mask = mask.to(DEVICE, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.autocast(
            device_type=DEVICE,
            enabled=(DEVICE == "cuda")
        ):
            pred = model(x)
            loss = masked_mse(pred, y, mask)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        train_loss += loss.item()

    model.eval()
    val_loss = 0.0

    with torch.no_grad():

        for x, y, mask in val_loader:

            x = x.to(DEVICE)
            y = y.to(DEVICE)
            mask = mask.to(DEVICE)

            with torch.autocast(
                device_type=DEVICE,
                enabled=(DEVICE == "cuda")
            ):
                pred = model(x)
                loss = masked_mse(pred, y, mask)

            val_loss += loss.item()

    train_loss /= len(train_loader)
    val_loss /= len(val_loader)

    print(
        f"Epoch {epoch + 1:02d}/{EPOCHS} | "
        f"Train: {train_loss:.6f} | "
        f"Val: {val_loss:.6f}"
    )

    if val_loss < best_val:
        best_val = val_loss

        torch.save(
            {
                "model": model.state_dict(),
                "val_loss": best_val
            },
            "checkpoints/best_model.pt"
        )

        print("✓ Best model saved")

print("\nTraining complete")
print(f"Best validation loss: {best_val:.6f}")