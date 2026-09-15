import math
import os
from pathlib import Path

import pandas as pd

class IcebergService:
    """Serves iceberg positions from the trained GRU prediction artifact."""
    
    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        default_path = project_root / "iceberg trajectory" / "outputs" / "iceberg" / "test_predictions.csv"
        self.predictions_path = Path(os.getenv("ICEBERG_PREDICTIONS_PATH", default_path))
        self.icebergs, self.forecast_date = self._load_predictions()

    def _load_predictions(self):
        required = {
            "track_id",
            "iceberg_id",
            "input_date",
            "target_date",
            "current_lat",
            "current_lon",
            "predicted_lat",
            "predicted_lon",
            "gru_error_km",
        }
        if not self.predictions_path.exists():
            raise FileNotFoundError(f"Iceberg GRU predictions not found: {self.predictions_path}")

        predictions = pd.read_csv(
            self.predictions_path,
            parse_dates=["input_date", "target_date"],
        )
        missing = required.difference(predictions.columns)
        if missing:
            raise ValueError(f"Iceberg GRU predictions missing columns: {sorted(missing)}")

        predictions = predictions.dropna(
            subset=[
                "current_lat",
                "current_lon",
                "predicted_lat",
                "predicted_lon",
            ]
        ).copy()
        predictions["target_date"] = predictions["target_date"].dt.normalize()
        forecast_date = predictions["target_date"].max()
        latest = predictions[predictions["target_date"] == forecast_date].copy()
        latest = latest.sort_values(["iceberg_id", "input_date", "track_id"])
        latest = latest.drop_duplicates("iceberg_id", keep="last")

        icebergs = []
        for row in latest.itertuples(index=False):
            speed_knots = self._speed_knots(
                row.current_lat,
                row.current_lon,
                row.predicted_lat,
                row.predicted_lon,
            )
            icebergs.append({
                "id": str(row.iceberg_id),
                "lat": float(row.current_lat),
                "lon": float(row.current_lon),
                "forecast_lat": float(row.predicted_lat),
                "forecast_lon": float(row.predicted_lon),
                "size_km2": None,
                "speed_knots": round(speed_knots, 3),
                "drift_dir": round(self._bearing(
                    row.current_lat,
                    row.current_lon,
                    row.predicted_lat,
                    row.predicted_lon,
                ), 1),
                "trajectory": [
                    [float(row.current_lon), float(row.current_lat)],
                    [float(row.predicted_lon), float(row.predicted_lat)],
                ],
                "prediction_date": str(forecast_date.date()),
                "prediction_error_km": round(float(row.gru_error_km), 3),
                "prediction_source": "iceberg_gru",
            })

        return icebergs, forecast_date.date().isoformat()

    @staticmethod
    def _distance_km(lat1, lon1, lat2, lon2):
        radius_km = 6371.0088
        lat1, lat2 = math.radians(lat1), math.radians(lat2)
        dlat = lat2 - lat1
        dlon = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2.0 * radius_km * math.asin(math.sqrt(a))

    @classmethod
    def _speed_knots(cls, lat1, lon1, lat2, lon2):
        return cls._distance_km(lat1, lon1, lat2, lon2) / 24.0 / 1.852

    @staticmethod
    def _bearing(lat1, lon1, lat2, lon2):
        lat1, lat2 = math.radians(lat1), math.radians(lat2)
        dlon = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
        bearing = math.degrees(math.atan2(
            math.sin(dlon) * math.cos(lat2),
            math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon),
        ))
        return (bearing + 360.0) % 360.0

    def get_all_icebergs(self):
        """Return latest observed positions and the GRU's 24-hour forecasts."""
        return self.icebergs

    def get_iceberg_risk_at(self, lat: float, lon: float) -> float:
        """Proximity penalty for nearby icebergs."""
        min_dist_km = float("inf")
        for berg in self.icebergs:
            dist = self._distance_km(lat, lon, berg["forecast_lat"], berg["forecast_lon"])
            if dist < min_dist_km:
                min_dist_km = dist

        risk_radius_km = 2.5 * 111.0
        if min_dist_km < risk_radius_km:
            return float(max(0.0, 1.0 - (min_dist_km / risk_radius_km)))
        return 0.0