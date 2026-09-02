from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_SRC_DIR = ROOT_DIR / "Sea ice prediction" / "src"
if str(MODEL_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_SRC_DIR))

from model import SeaIceConvLSTM


class SeaIceMLService:

    def __init__(
        self,
        model_path=None,
        data_path=None,
        dates_path=None,
        lat_path=None,
        lon_path=None,
    ):
        project_root = ROOT_DIR
        self.model_path = Path(model_path) if model_path else project_root / "Sea ice prediction" / "checkpoints" / "best_model.pt"
        self.data_path = Path(data_path) if data_path else project_root / "Sea ice prediction" / "data" / "processed" / "sic.npy"
        self.dates_path = Path(dates_path) if dates_path else project_root / "Sea ice prediction" / "data" / "processed" / "dates.npy"
        self.lat_path = Path(lat_path) if lat_path else project_root / "Sea ice prediction" / "data" / "processed" / "lat.npy"
        self.lon_path = Path(lon_path) if lon_path else project_root / "Sea ice prediction" / "data" / "processed" / "lon.npy"

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.seq_len = 7
        self.size = 128

        self.data = np.load(
            self.data_path,
            mmap_mode="r"
        )

        self.dates = np.load(
            self.dates_path
        )

        self.lat_grid = self._load_geographic_grid(self.lat_path, self.lon_path)
        self.lon_grid = self.lat_grid[1] if isinstance(self.lat_grid, tuple) else None

        self.model = SeaIceConvLSTM(
            hidden=16
        ).to(self.device)

        checkpoint = torch.load(
            str(self.model_path),
            map_location=self.device
        )

        self.model.load_state_dict(
            checkpoint["model"]
        )

        self.model.eval()

        self.prediction = None
        self.forecast_date = None

        print(
            f"[SEA ICE ML] Loaded {len(self.dates)} observations"
        )

        print(
            f"[SEA ICE ML] Device: {self.device}"
        )

    def _load_geographic_grid(self, lat_path: Path, lon_path: Path):
        if lat_path.exists() and lon_path.exists():
            lat = np.load(lat_path)
            lon = np.load(lon_path)
            if lat.ndim == 2 and lon.ndim == 2:
                lat_grid = np.asarray(lat, dtype=np.float32)
                lon_grid = np.asarray(lon, dtype=np.float32)
                if lat_grid.shape != (self.size, self.size):
                    lat_grid = np.linspace(np.nanmin(lat_grid), np.nanmax(lat_grid), self.size)
                    lon_grid = np.linspace(np.nanmin(lon_grid), np.nanmax(lon_grid), self.size)
                    lat_grid, lon_grid = np.meshgrid(lat_grid, lon_grid)
                return lat_grid, lon_grid
        lat_axis = np.linspace(-90.0, -39.0, self.size)
        lon_axis = np.linspace(-180.0, 180.0, self.size)
        return np.meshgrid(lat_axis, lon_axis)

    def _prepare_sequence(self, target_idx):

        if target_idx < self.seq_len:
            raise ValueError(
                "Not enough history for 7-day forecast."
            )

        dates = self.dates[
            target_idx - self.seq_len:
            target_idx
        ]

        gaps = (
            np.diff(dates)
            .astype("timedelta64[D]")
            .astype(int)
        )

        if not np.all(gaps == 1):
            raise ValueError(
                "Forecast input contains missing days."
            )

        window = np.asarray(
            self.data[
                target_idx - self.seq_len:
                target_idx
            ],
            dtype=np.float32
        )

        window = np.nan_to_num(
            window,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        x = torch.from_numpy(
            window
        ).unsqueeze(1)

        x = F.interpolate(
            x,
            size=(self.size, self.size),
            mode="bilinear",
            align_corners=False
        )

        x = (
            x
            .squeeze(1)
            .unsqueeze(0)
            .unsqueeze(2)
            .to(self.device)
        )

        return x


    def forecast(self, date):

        target_date = np.datetime64(
            date,
            "D"
        )

        matches = np.where(
            self.dates.astype("datetime64[D]")
            == target_date
        )[0]

        if len(matches) == 0:
            date_deltas = np.abs(self.dates.astype("datetime64[D]") - target_date)
            nearest_idx = int(np.argmin(date_deltas))
            target_date = self.dates[nearest_idx]
            target_idx = nearest_idx
        else:
            target_idx = int(matches[0])

        x = self._prepare_sequence(
            target_idx
        )

        with torch.no_grad():

            prediction = self.model(x)

        prediction = (
            prediction
            .squeeze()
            .cpu()
            .numpy()
        )

        self.prediction = prediction
        self.forecast_date = target_date

        return prediction

    def get_risk_at(self, lat: float, lon: float) -> float:
        if self.prediction is None:
            self.forecast(np.datetime64("now", "D").astype(str))

        if isinstance(self.lat_grid, tuple):
            lat_grid, lon_grid = self.lat_grid
            if lat_grid.shape != self.prediction.shape:
                lat_axis = np.linspace(np.nanmin(lat_grid), np.nanmax(lat_grid), self.prediction.shape[0])
                lon_axis = np.linspace(np.nanmin(lon_grid), np.nanmax(lon_grid), self.prediction.shape[1])
                lat_grid, lon_grid = np.meshgrid(lat_axis, lon_axis)
            dist = (lat_grid - lat) ** 2 + (lon_grid - lon) ** 2
            idx = np.unravel_index(np.argmin(dist), dist.shape)
            return float(np.clip(self.prediction[idx], 0.0, 1.0))

        return float(np.clip(self.prediction.mean(), 0.0, 1.0))