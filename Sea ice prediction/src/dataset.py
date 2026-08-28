import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset


class SeaIceDataset(Dataset):
    def __init__(self, data_path, dates_path, seq_len=7, size=128):
        data = np.load(data_path, mmap_mode="r")
        dates = np.load(dates_path)
        self.data = data
        self.size = size
        self.seq_len = seq_len

        gaps = np.diff(dates).astype("timedelta64[D]").astype(int)

        self.indices = [
            i for i in range(len(self.data) - seq_len)
            if np.all(gaps[i:i + seq_len] == 1)
        ]

        print(
            f"Loaded {len(self.data)} days | "
            f"Resolution: {size}×{size} | "
            f"Valid sequences: {len(self.indices)}"
        )

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        i = self.indices[idx]

        window = np.asarray(self.data[i:i + self.seq_len + 1], dtype=np.float32)
        valid = np.isfinite(window)
        window = np.nan_to_num(window, nan=0.0, posinf=0.0, neginf=0.0)

        values = torch.from_numpy(window).unsqueeze(1)
        validity = torch.from_numpy(valid.astype(np.float32)).unsqueeze(1)

        values = F.interpolate(
            values,
            size=(self.size, self.size),
            mode="bilinear",
            align_corners=False
        ).squeeze(1)

        validity = F.interpolate(
            validity,
            size=(self.size, self.size),
            mode="nearest"
        ).squeeze(1)

        x = values[:self.seq_len].unsqueeze(1)
        y = values[self.seq_len].unsqueeze(0)
        mask = validity[self.seq_len].unsqueeze(0)

        return x, y, mask