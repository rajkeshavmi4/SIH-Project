import torch
import torch.nn as nn


class ConvLSTMCell(nn.Module):
    def __init__(self, in_channels, hidden_channels, kernel_size=3):
        super().__init__()

        self.hidden_channels = hidden_channels
        padding = kernel_size // 2

        self.conv = nn.Conv2d(
            in_channels + hidden_channels,
            4 * hidden_channels,
            kernel_size,
            padding=padding
        )

    def forward(self, x, state):
        h, c = state

        gates = self.conv(torch.cat([x, h], dim=1))
        i, f, o, g = gates.chunk(4, dim=1)

        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        o = torch.sigmoid(o)
        g = torch.tanh(g)

        c = f * c + i * g
        h = o * torch.tanh(c)

        return h, c

    def init_state(self, batch, height, width, device):
        shape = (batch, self.hidden_channels, height, width)

        return (
            torch.zeros(shape, device=device),
            torch.zeros(shape, device=device)
        )


class SeaIceConvLSTM(nn.Module):
    def __init__(self, hidden=16):
        super().__init__()

        self.layer1 = ConvLSTMCell(1, hidden)
        self.layer2 = ConvLSTMCell(hidden, hidden)

        self.head = nn.Conv2d(hidden, 1, kernel_size=1)

    def forward(self, x):
        # x: (B, T, 1, H, W)

        batch, steps, _, height, width = x.shape

        state1 = self.layer1.init_state(
            batch, height, width, x.device
        )

        state2 = self.layer2.init_state(
            batch, height, width, x.device
        )

        for t in range(steps):
            h1, c1 = self.layer1(x[:, t], state1)
            state1 = (h1, c1)

            h2, c2 = self.layer2(h1, state2)
            state2 = (h2, c2)

        return torch.sigmoid(self.head(h2))