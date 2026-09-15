import math
import os
import time
from datetime import datetime

from backend.iceberg_service import IcebergService
from backend.ml_risk_model import PolarMLRiskModel
from backend.sea_ice_service import SeaIceService
from backend.live_data_service import LiveEnvironmentService


class RiskEngine:
    def __init__(self, sea_ice_srv: SeaIceService, iceberg_srv: IcebergService, sea_ice_ml=None, live_env_srv: LiveEnvironmentService = None):
        self.ice_srv = sea_ice_srv
        self.berg_srv = iceberg_srv
        self.sea_ice_ml = sea_ice_ml
        self.live_env_srv = live_env_srv or LiveEnvironmentService()
        self.ml_model = PolarMLRiskModel()  # ML Model Loaded
        self._risk_cache = {}
        self._risk_cache_ttl_seconds = 60

    def get_weather_risk(self, lat: float, lon: float) -> float:
        if os.getenv("POLAR_ROUTE_USE_LIVE_WEATHER", "0") == "1":
            live = self.live_env_srv.fetch_live_metocean(lat, lon)
            wind_kt = live.get("wind_speed_knots", 20.0)
            wave_m = live.get("wave_height_m", 2.0)
            vis_km = live.get("visibility_km", 10.0)
        else:
            # Route search evaluates many grid cells; keep it independent of
            # network latency while the live endpoint remains available for telemetry.
            wind_kt = 12.0 + math.sin(math.radians(lon * 3)) * 6.0 + abs(lat + 60.0) * 0.5
            wave_m = 0.8 + (wind_kt / 40.0) * 3.5
            vis_km = max(1.5, 18.0 - (wind_kt * 0.2))
        
        # Multi-variable MetOcean weather risk index calculation
        wind_penalty = min(1.0, wind_kt / 50.0)
        wave_penalty = min(1.0, wave_m / 8.0)
        vis_penalty = max(0.0, 1.0 - (vis_km / 15.0))
        
        storm_belt = math.exp(-((lat - -60.0)**2) / 18.0)
        base_weather = float(min(1.0, max(0.1, storm_belt * 0.4 + 0.3 * wind_penalty + 0.2 * wave_penalty + 0.1 * vis_penalty)))
        return base_weather

    def get_ml_ice_risk(self, lat: float, lon: float, departure_date: str = None) -> float:
        month = 11
        if departure_date:
            try:
                month = datetime.strptime(departure_date, "%Y-%m-%d").month
            except ValueError:
                pass
        if self.sea_ice_ml is not None:
                return float(max(0.0, min(1.0, self.sea_ice_ml.get_risk_at(lat, lon, departure_date))))
        return self.ml_model.predict_environmental_risk(lat, lon, month=month)

    def calculate_cell_risk(self, lat: float, lon: float, vessel_type: str = "Polar Class 4 (Medium)", departure_date: str = None) -> dict:
        cache_key = (round(lat, 2), round(lon, 2), vessel_type, departure_date)
        cached = self._risk_cache.get(cache_key)
        now = time.monotonic()
        if cached and now - cached[0] < self._risk_cache_ttl_seconds:
            return cached[1].copy()

        # 1. ML Model Inference for Sea-Ice Concentration Forecast
        ml_ice_risk = self.get_ml_ice_risk(lat, lon, departure_date)

        # 2. Iceberg Proximity & Multi-Variable MetOcean Weather
        berg_risk = self.berg_srv.get_iceberg_risk_at(lat, lon)
        weather_risk = self.get_weather_risk(lat, lon)

        # 3. Dynamic Real-Time Active Hazards (Drifting iceberg alerts / sudden ice surges)
        dynamic_hazard_risk = self.live_env_srv.get_dynamic_hazard_risk_at(lat, lon)

        # Vessel capability attenuation
        vessel_factor = 1.0
        if "Class 1" in vessel_type:
            vessel_factor = 0.45
        elif "Class 4" in vessel_type:
            vessel_factor = 0.75
        elif "Standard" in vessel_type:
            vessel_factor = 1.35

        raw_risk = (0.4 * ml_ice_risk + 0.25 * berg_risk + 0.15 * weather_risk + 0.20 * dynamic_hazard_risk) * vessel_factor
        composite_risk = float(min(1.0, max(0.0, raw_risk)))

        result = {
            "total_risk": composite_risk,
            "sea_ice_risk": ml_ice_risk,
            "iceberg_risk": max(berg_risk, dynamic_hazard_risk),
            "weather_risk": weather_risk,
            "dynamic_hazard_risk": dynamic_hazard_risk
        }
        self._risk_cache[cache_key] = (now, result)
        return result.copy()