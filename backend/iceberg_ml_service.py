import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch


ICEBERG_SRC = Path(__file__).resolve().parent.parent / "iceberg trajectory" / "src"
if str(ICEBERG_SRC) not in sys.path:
	sys.path.insert(0, str(ICEBERG_SRC))

from iceberg_model import IcebergGRU


EARTH_RADIUS_KM = 6371.0
SEQ_LEN = 7
HORIZONS_HOURS = [24, 48, 72]
FEATURE_COLUMNS = ["latitude", "longitude", "delta_lat", "delta_lon", "speed_kmh"]
FEATURED_ICEBERGS = ["a76c", "d15c", "b09g", "a81", "d33c", "a83"]
MOVING_SPEED_THRESHOLD_KMH = 0.1
MODEL_COLLAPSE_RATIO = 0.5


def destination_from_displacement(origin, north_km, east_km):
	lat, lon = origin
	lat_rad = np.radians(lat)
	new_lat = lat + (north_km / EARTH_RADIUS_KM) * (180.0 / np.pi)
	new_lon = lon + (east_km / (EARTH_RADIUS_KM * np.cos(lat_rad))) * (180.0 / np.pi)
	return float(new_lat), float(new_lon)


class IcebergMLService:
	def __init__(self, features_csv=None, checkpoint_path=None):
		base = Path(__file__).resolve().parent.parent / "iceberg trajectory"
		features_csv = features_csv or base / "data" / "processed" / "trajectory_features.csv"
		checkpoint_path = checkpoint_path or base / "checkpoints" / "iceberg_gru_72h_best.pt"

		self.df = pd.read_csv(features_csv, parse_dates=["date"])
		self.df["delta_lon"] = (self.df["delta_lon"] + 180.0) % 360.0 - 180.0
		self.iceberg_ids = sorted(self.df["iceberg_id"].dropna().unique())
		self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

		checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
		self.mean = np.asarray(checkpoint["mean"], dtype=np.float32)
		self.std = np.asarray(checkpoint["std"], dtype=np.float32)

		self.model = IcebergGRU().to(self.device)
		self.model.load_state_dict(checkpoint["model"])
		self.model.eval()

		print(
			f"[ICEBERG ML] Loaded {len(self.df):,} rows, "
			f"{self.df['iceberg_id'].nunique():,} icebergs"
		)

	def _get_sequence(self, iceberg_id):
		rows = self.df[self.df["iceberg_id"] == iceberg_id].sort_values("date")
		if len(rows) < SEQ_LEN:
			return None
		recent = rows.tail(SEQ_LEN)
		features = recent[FEATURE_COLUMNS].values.astype(np.float32)
		return features, recent.iloc[-1]

	@staticmethod
	def _observed_motion(rows):
		recent = rows.tail(3)
		lat = recent["latitude"].to_numpy(dtype=np.float32)
		lon = recent["longitude"].to_numpy(dtype=np.float32)
		lat_change = np.diff(lat) * (np.pi / 180.0) * EARTH_RADIUS_KM
		lon_change = np.diff(lon) * (np.pi / 180.0) * EARTH_RADIUS_KM * np.cos(np.radians(lat[1:]))
		return np.median(np.column_stack([lat_change, lon_change]), axis=0)

	def predict_trajectory(self, iceberg_id):
		sequence = self._get_sequence(iceberg_id)
		if sequence is None:
			return None

		features, last_row = sequence
		normalized = (features - self.mean) / self.std
		inputs = torch.from_numpy(normalized).unsqueeze(0).to(self.device)

		with torch.no_grad():
			output = self.model(inputs)

		displacements = output.squeeze(0).cpu().numpy()
		rows = self.df[self.df["iceberg_id"] == iceberg_id].sort_values("date")
		recent_motion = self._observed_motion(rows)
		recent_speed = float(rows.tail(3)["speed_kmh"].median())
		model_24h_distance = float(np.linalg.norm(displacements[0]))
		recent_24h_distance = float(np.linalg.norm(recent_motion))
		used_motion_fallback = (
			recent_speed >= MOVING_SPEED_THRESHOLD_KMH
			and recent_24h_distance > 0.0
			and model_24h_distance < recent_24h_distance * MODEL_COLLAPSE_RATIO
		)
		if used_motion_fallback:
			displacements = np.asarray(
				[recent_motion * (hours / 24.0) for hours in HORIZONS_HOURS],
				dtype=np.float32,
			)
		origin = (float(last_row["latitude"]), float(last_row["longitude"]))
		trajectory = [[origin[1], origin[0]]]

		for displacement in displacements:
			new_lat, new_lon = destination_from_displacement(
				origin,
				float(displacement[0]),
				float(displacement[1]),
			)
			trajectory.append([round(new_lon, 3), round(new_lat, 3)])

		return {
			"id": iceberg_id,
			"lat": origin[0],
			"lon": origin[1],
			"last_observed_date": str(last_row["date"].date()),
			"trajectory": trajectory,
			"source": (
				"GRU model with observed-motion continuity correction"
				if used_motion_fallback
				else "GRU model (real historical trajectory)"
			),
		}

	def get_all_icebergs(self):
		return [
			prediction
			for iceberg_id in self.iceberg_ids
			if (prediction := self.predict_trajectory(iceberg_id)) is not None
		]

	def get_featured_icebergs(self):
		return [
			prediction
			for iceberg_id in FEATURED_ICEBERGS
			if (prediction := self.predict_trajectory(iceberg_id)) is not None
		]
