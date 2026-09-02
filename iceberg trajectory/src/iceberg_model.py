import torch
import torch.nn as nn


class IcebergGRU(nn.Module):

    def __init__(
        self,
        input_size=5,
        hidden_size=128,
        layers=2,
        dropout=0.15
    ):
        super().__init__()

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0
        )

        self.head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 6)
        )

    def forward(self, x):

        out, _ = self.gru(x)

        h = out[:, -1]

        output = self.head(h)

        return output.reshape(
            -1,
            3,
            2
        )