from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F
from scipy.ndimage import zoom

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
        ) if self.data_path.exists() else None

        self.dates = np.load(self.dates_path) if self.dates_path.exists() else np.array([], dtype="datetime64[D]")

        self.lat_grid = self._load_geographic_grid(self.lat_path, self.lon_path)
        self.lon_grid = self.lat_grid[1] if isinstance(self.lat_grid, tuple) else None

        self.model = None
        if self.model_path.exists():
            self.model = SeaIceConvLSTM(hidden=16).to(self.device)
            checkpoint = torch.load(str(self.model_path), map_location=self.device)
            self.model.load_state_dict(checkpoint["model"])
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
                    zoom_y = self.size / lat_grid.shape[0]
                    zoom_x = self.size / lat_grid.shape[1]
                    lat_grid = zoom(lat_grid, (zoom_y, zoom_x), order=1)
                    lon_grid = zoom(lon_grid, (zoom_y, zoom_x), order=1)
                return lat_grid, lon_grid
        lat_axis = np.linspace(-90.0, -39.0, self.size)
        lon_axis = np.linspace(-180.0, 180.0, self.size)
        return np.meshgrid(lat_axis, lon_axis, indexing="ij")

    def _prepare_sequence(self, target_idx):
        if target_idx < self.seq_len:
            raise ValueError("Not enough history for 7-day forecast.")
        dates = self.dates[target_idx - self.seq_len: target_idx]
        gaps = np.diff(dates).astype("timedelta64[D]").astype(int)
        if not np.all(gaps == 1):
            raise ValueError("Forecast input contains missing days.")

        window = np.asarray(self.data[target_idx - self.seq_len: target_idx], dtype=np.float32)
        valid = np.isfinite(window).astype(np.float32)
        window = np.nan_to_num(window, nan=0.0, posinf=0.0, neginf=0.0)

        values = torch.from_numpy(window).unsqueeze(1)
        validity = torch.from_numpy(valid).unsqueeze(1)

        weighted_values = values * validity
        weighted_values = F.interpolate(weighted_values, size=(self.size, self.size), mode="bilinear", align_corners=False)
        validity_resized = F.interpolate(validity, size=(self.size, self.size), mode="bilinear", align_corners=False)

        safe_validity = validity_resized.clamp(min=1e-6)
        values_resized = weighted_values / safe_validity
        validity_mask = (validity_resized > 0.5).float()

        x = values_resized.squeeze(1).unsqueeze(0).unsqueeze(2).to(self.device)
        land_mask = validity_mask[-1, 0].cpu().numpy()
        return x, land_mask


    def forecast(self, date):

        target_date = np.datetime64(
            date,
            "D"
        )

        if self.model is None or self.data is None or len(self.dates) == 0:
            lat_grid, lon_grid = self.lat_grid
            seasonal = 0.5 + 0.45 * np.cos((target_date.astype("datetime64[M]").astype(int) % 12) * np.pi / 6.0)
            latitude_factor = np.clip((-lat_grid - 55.0) / 35.0, 0.0, 1.0)
            prediction = np.clip(latitude_factor * seasonal, 0.0, 1.0).astype(np.float32)
        else:
            land_mask = None
            matches = np.where(self.dates.astype("datetime64[D]") == target_date)[0]
            if len(matches) == 0:
                date_deltas = np.abs(self.dates.astype("datetime64[D]") - target_date)
                nearest_idx = int(np.argmin(date_deltas))
                target_date = self.dates[nearest_idx]
                target_idx = nearest_idx
            else:
                target_idx = int(matches[0])

            x, land_mask = self._prepare_sequence(target_idx)
            with torch.no_grad():
                prediction = self.model(x)
            prediction = prediction.squeeze().cpu().numpy()

        self.prediction = prediction
        self.forecast_date = target_date
        self.land_mask = land_mask

        return prediction

    def get_risk_at(self, lat: float, lon: float, forecast_date=None) -> float:
        if forecast_date is not None:
            requested_date = np.datetime64(forecast_date, "D")
            loaded_date = self.forecast_date.astype("datetime64[D]") if self.forecast_date is not None else None
            if len(self.dates) and requested_date not in self.dates.astype("datetime64[D]"):
                requested_date = self.dates[np.argmin(np.abs(self.dates.astype("datetime64[D]") - requested_date))]
            if self.prediction is None or loaded_date != requested_date:
                self.forecast(requested_date.astype(str))
        elif self.prediction is None:
            self.forecast(np.datetime64("now", "D").astype(str))

        if isinstance(self.lat_grid, tuple):
            lat_grid, lon_grid = self.lat_grid
            if lat_grid.shape != self.prediction.shape:
                lat_axis = np.linspace(np.nanmin(lat_grid), np.nanmax(lat_grid), self.prediction.shape[0])
                lon_axis = np.linspace(np.nanmin(lon_grid), np.nanmax(lon_grid), self.prediction.shape[1])
                lat_grid, lon_grid = np.meshgrid(lat_axis, lon_axis, indexing="ij")
            dist = (lat_grid - lat) ** 2 + (lon_grid - lon) ** 2
            idx = np.unravel_index(np.argmin(dist), dist.shape)
            if hasattr(self, "land_mask") and self.land_mask is not None and self.land_mask[idx] < 0.5:
                return 1.0  # land or no-data: treat as maximum risk, never "safe"
            return float(np.clip(self.prediction[idx], 0.0, 1.0))

        return float(np.clip(self.prediction.mean(), 0.0, 1.0))