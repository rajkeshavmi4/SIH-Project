from pathlib import Path
import random
import numpy as np
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader

from iceberg_model import IcebergGRU

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

DATA = Path("data/processed/iceberg_ml")
CHECKPOINT = Path("checkpoints/iceberg_gru_best.pt")

BATCH = 256
EPOCHS = 40
LR = 1e-3
PATIENCE = 7

X_train = np.load(DATA / "X_train.npy")
X_val = np.load(DATA / "X_val.npy")

Y_train = np.load(DATA / "Y_1d_train.npy")
Y_val = np.load(DATA / "Y_1d_val.npy")

mean = X_train.reshape(-1, X_train.shape[-1]).mean(0)
std = X_train.reshape(-1, X_train.shape[-1]).std(0)
std = np.maximum(std, 1e-6)

X_train = (X_train - mean) / std
X_val = (X_val - mean) / std

train_ds = TensorDataset(
    torch.from_numpy(X_train),
    torch.from_numpy(Y_train)
)

val_ds = TensorDataset(
    torch.from_numpy(X_val),
    torch.from_numpy(Y_val)
)

train_loader = DataLoader(
    train_ds,
    batch_size=BATCH,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_ds,
    batch_size=BATCH,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

model = IcebergGRU().to(DEVICE)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=1e-4
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=3
)

loss_fn = nn.SmoothL1Loss()

best = float("inf")
wait = 0

print(f"Device: {DEVICE}")
print(f"Train sequences: {len(X_train):,}")
print(f"Val sequences:   {len(X_val):,}")

for epoch in range(1, EPOCHS + 1):

    model.train()
    train_loss = 0

    for x, y in train_loader:

        x = x.to(DEVICE)
        y = y.to(DEVICE)

        optimizer.zero_grad()

        pred = model(x)

        loss = loss_fn(pred, y)

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            1.0
        )

        optimizer.step()

        train_loss += loss.item() * len(x)

    train_loss /= len(train_ds)

    model.eval()
    val_loss = 0

    with torch.no_grad():

        for x, y in val_loader:

            x = x.to(DEVICE)
            y = y.to(DEVICE)

            pred = model(x)

            val_loss += (
                loss_fn(pred, y).item() * len(x)
            )

    val_loss /= len(val_ds)

    scheduler.step(val_loss)

    print(
        f"Epoch {epoch:02d}/{EPOCHS} | "
        f"Train: {train_loss:.7f} | "
        f"Val: {val_loss:.7f}"
    )

    if val_loss < best:

        best = val_loss
        wait = 0

        CHECKPOINT.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        torch.save(
            {
                "model": model.state_dict(),
                "mean": mean,
                "std": std,
                "val_loss": val_loss
            },
            CHECKPOINT
        )

        print("✓ Best model saved")

    else:
        wait += 1

    if wait >= PATIENCE:

        print("Early stopping")

        break

print(f"\nBest validation loss: {best:.7f}")
print(f"Saved → {CHECKPOINT}")