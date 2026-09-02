import math

from backend.iceberg_service import IcebergService
from backend.ml_risk_model import PolarMLRiskModel
from backend.sea_ice_service import SeaIceService


class RiskEngine:
    def __init__(self, sea_ice_srv: SeaIceService, iceberg_srv: IcebergService, sea_ice_ml=None):
        self.ice_srv = sea_ice_srv
        self.berg_srv = iceberg_srv
        self.sea_ice_ml = sea_ice_ml
        self.ml_model = PolarMLRiskModel()  # ML Model Loaded

    def get_weather_risk(self, lat: float, lon: float) -> float:
        storm_belt = math.exp(-((lat - -60.0)**2) / 18.0)
        cyclonic_eddy = 0.3 * math.sin(math.radians(lon * 2.5))
        return float(min(1.0, max(0.1, storm_belt * 0.7 + cyclonic_eddy)))

    def get_ml_ice_risk(self, lat: float, lon: float) -> float:
        if self.sea_ice_ml is not None:
            return float(max(0.0, min(1.0, self.sea_ice_ml.get_risk_at(lat, lon))))
        return self.ml_model.predict_environmental_risk(lat, lon, month=11)

    def calculate_cell_risk(self, lat: float, lon: float, vessel_type: str = "Polar Class 4 (Medium)") -> dict:
        # 1. ML Model Inference for Ice Severity Prediction
        ml_ice_risk = self.get_ml_ice_risk(lat, lon)

        # 2. Iceberg Proximity & MetOcean Weather
        berg_risk = self.berg_srv.get_iceberg_risk_at(lat, lon)
        weather_risk = self.get_weather_risk(lat, lon)

        # Vessel capability attenuation
        vessel_factor = 1.0
        if "Class 1" in vessel_type:
            vessel_factor = 0.45
        elif "Class 4" in vessel_type:
            vessel_factor = 0.75
        elif "Standard" in vessel_type:
            vessel_factor = 1.35

        composite_risk = (0.5 * ml_ice_risk + 0.3 * berg_risk + 0.2 * weather_risk) * vessel_factor
        composite_risk = float(min(1.0, max(0.0, composite_risk)))

        return {
            "total_risk": composite_risk,
            "sea_ice_risk": ml_ice_risk,
            "iceberg_risk": berg_risk,
            "weather_risk": weather_risk
        }