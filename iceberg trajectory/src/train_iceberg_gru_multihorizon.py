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

CHECKPOINT = Path(
    "checkpoints/iceberg_gru_72h_best.pt"
)

BATCH_SIZE = 256
EPOCHS = 40
LR = 1e-3
PATIENCE = 7


# ============================================================
# LOAD
# ============================================================

X_train = np.load(
    DATA / "X_train.npy"
).astype(np.float32)

X_val = np.load(
    DATA / "X_val.npy"
).astype(np.float32)

Y_train = np.stack(
    [
        np.load(DATA / "Y_1d_train.npy"),
        np.load(DATA / "Y_2d_train.npy"),
        np.load(DATA / "Y_3d_train.npy")
    ],
    axis=1
).astype(np.float32)

Y_val = np.stack(
    [
        np.load(DATA / "Y_1d_val.npy"),
        np.load(DATA / "Y_2d_val.npy"),
        np.load(DATA / "Y_3d_val.npy")
    ],
    axis=1
).astype(np.float32)


# ============================================================
# NORMALIZATION
# ============================================================

mean = X_train.reshape(
    -1,
    X_train.shape[-1]
).mean(axis=0)

std = X_train.reshape(
    -1,
    X_train.shape[-1]
).std(axis=0)

std = np.maximum(
    std,
    1e-6
)

X_train = (
    X_train - mean
) / std

X_val = (
    X_val - mean
) / std


# ============================================================
# DATA LOADERS
# ============================================================

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
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_ds,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# MODEL
# ============================================================

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

best_loss = float("inf")
wait = 0


print("=" * 60)
print("ICEBERG MULTI-HORIZON GRU")
print("=" * 60)

print(f"Device          : {DEVICE}")
print(f"Train sequences : {len(X_train):,}")
print(f"Val sequences   : {len(X_val):,}")


# ============================================================
# TRAIN
# ============================================================

for epoch in range(
    1,
    EPOCHS + 1
):

    model.train()

    train_loss = 0.0

    for x, y in train_loader:

        x = x.to(DEVICE)
        y = y.to(DEVICE)

        optimizer.zero_grad()

        pred = model(x)

        loss = loss_fn(
            pred,
            y
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            1.0
        )

        optimizer.step()

        train_loss += (
            loss.item()
            * len(x)
        )

    train_loss /= len(train_ds)


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    val_loss = 0.0

    with torch.no_grad():

        for x, y in val_loader:

            x = x.to(DEVICE)
            y = y.to(DEVICE)

            pred = model(x)

            loss = loss_fn(
                pred,
                y
            )

            val_loss += (
                loss.item()
                * len(x)
            )

    val_loss /= len(val_ds)

    scheduler.step(
        val_loss
    )


    print(
        f"Epoch {epoch:02d}/{EPOCHS} | "
        f"Train: {train_loss:.7f} | "
        f"Val: {val_loss:.7f}"
    )


    # --------------------------------------------------------
    # CHECKPOINT
    # --------------------------------------------------------

    if val_loss < best_loss:

        best_loss = val_loss
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

        print(
            "✓ Best model saved"
        )

    else:

        wait += 1

    if wait >= PATIENCE:

        print(
            "Early stopping"
        )

        break


print("\n" + "=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print(
    f"Best validation loss: "
    f"{best_loss:.7f}"
)

print(
    f"Saved → {CHECKPOINT}"
)