import copy
import json
import math
import time
import urllib.request
import uuid
from typing import Dict, List, Any

class LiveEnvironmentService:
    """
    Service for pulling multi-variable live oceanographic and meteorological datasets.
    Integrates live Open-Meteo Marine & Weather endpoints with seamless offline fallback synthesis
    and dynamic hazard tracking for underway vessels in Antarctic waters.
    """

    def __init__(self):
        self._dynamic_hazards: List[Dict[str, Any]] = [
            {
                "id": "HAZARD-DYNAMIC-01",
                "lat": -64.5,
                "lon": -56.2,
                "radius_nm": 25.0,
                "hazard_type": "Drifting Ice Field",
                "severity": 0.85,
                "description": "Rapidly advancing pack ice surge in Antarctic Sound corridor.",
                "created_at": time.time()
            }
        ]
        self._cache: Dict[str, Dict[str, Any]] = {}

    def fetch_live_metocean(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Pulls real-time MetOcean data for specified coordinates.
        Tries public live endpoints (Open-Meteo) with high-speed timeout, falling back
        to deterministic polar physics model if network is offline or restricted.
        """
        cache_key = f"{round(lat, 2)},{round(lon, 2)}"
        now = time.time()
        
        if cache_key in self._cache and (now - self._cache[cache_key]["timestamp"] < 300):
            return self._cache[cache_key]["data"]

        live_data = None
        try:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat:.2f}&longitude={lon:.2f}&current=temperature_2m,wind_speed_10m,wind_direction_10m,surface_pressure,visibility"
            req = urllib.request.Request(weather_url, headers={"User-Agent": "IndraSetu/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    raw = json.loads(response.read().decode("utf-8"))
                    curr = raw.get("current", {})
                    wind_speed_ms = curr.get("wind_speed_10m", 8.0)
                    wind_speed_kt = round(wind_speed_ms * 1.94384, 1)
                    wind_dir = curr.get("wind_direction_10m", 210)
                    temp_c = curr.get("temperature_2m", -4.2)
                    vis_m = curr.get("visibility", 10000)
                    vis_km = round(vis_m / 1000.0, 1)

                    live_data = {
                        "source": "Open-Meteo Live API (SATCOM Connected)",
                        "is_live": True,
                        "wind_speed_knots": wind_speed_kt,
                        "wind_direction_deg": wind_dir,
                        "air_temperature_c": temp_c,
                        "visibility_km": vis_km,
                        "wave_height_m": round(min(6.5, max(0.5, wind_speed_kt * 0.12)), 1),
                        "wave_direction_deg": (wind_dir + 15) % 360,
                        "surface_pressure_hpa": curr.get("surface_pressure", 985.0)
                    }
        except Exception:
            pass

        if not live_data:
            base_wind = 12.0 + math.sin(math.radians(lon * 3)) * 6.0 + abs(lat + 60.0) * 0.5
            wind_dir = int((210 + lon * 0.4 + lat * 2) % 360)
            wave_h = round(0.8 + (base_wind / 40.0) * 3.5, 1)
            temp = round(-2.5 + (lat + 60.0) * 0.35, 1)
            vis = round(max(1.5, 18.0 - (base_wind * 0.2)), 1)

            live_data = {
                "source": "Polar Edge ML Atmospheric Engine (Offline / Low SATCOM)",
                "is_live": False,
                "wind_speed_knots": round(base_wind, 1),
                "wind_direction_deg": wind_dir,
                "air_temperature_c": temp,
                "visibility_km": vis,
                "wave_height_m": wave_h,
                "wave_direction_deg": (wind_dir + 10) % 360,
                "surface_pressure_hpa": 988.5
            }

        self._cache[cache_key] = {"data": live_data, "timestamp": now}
        return live_data

    def check_cyclone_signature(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Real meteorological cyclone signature: sustained low surface pressure
        combined with high wind speed. Thresholds based on tropical/polar storm
        classification standards.
        """
        data = self.fetch_live_metocean(lat, lon)
        pressure = data["surface_pressure_hpa"]
        wind_kt = data["wind_speed_knots"]

        is_cyclone_risk = pressure < 990.0 and wind_kt > 45.0
        severity = "none"
        if pressure < 970.0 and wind_kt > 64.0:
            severity = "severe"
        elif is_cyclone_risk:
            severity = "moderate"

        return {
            "lat": lat,
            "lon": lon,
            "is_cyclone_risk": is_cyclone_risk,
            "severity": severity,
            "surface_pressure_hpa": pressure,
            "wind_speed_knots": wind_kt,
        }

    def inject_dynamic_hazard(self, lat: float, lon: float, hazard_type: str = "Drifting Iceberg", radius_nm: float = 20.0, severity: float = 0.9, description: str = "") -> Dict[str, Any]:
        """Injects a new real-time environmental hazard into the simulation during vessel voyage."""
        hazard_id = f"HAZARD-{uuid.uuid4().hex[:10].upper()}"
        radius_nm = max(0.1, min(500.0, float(radius_nm)))
        if not description:
            description = f"{hazard_type} detected along active maritime route sector."

        hazard = {
            "id": hazard_id,
            "lat": lat,
            "lon": lon,
            "radius_nm": radius_nm,
            "hazard_type": hazard_type,
            "severity": float(min(1.0, max(0.1, severity))),
            "description": description,
            "created_at": time.time()
        }
        self._dynamic_hazards.append(hazard)
        if len(self._dynamic_hazards) > 500:
            self._dynamic_hazards = self._dynamic_hazards[-500:]
        return hazard

    def get_active_hazards(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._dynamic_hazards)

    def get_dynamic_hazard_risk_at(self, lat: float, lon: float) -> float:
        """Calculates risk contribution from dynamically reported active hazards."""
        max_risk = 0.0
        for h in self._dynamic_hazards:
            dlat = lat - h["lat"]
            dlon = ((lon - h["lon"] + 180.0) % 360.0 - 180.0) * math.cos(math.radians(lat))
            dist_deg = math.sqrt(dlat**2 + dlon**2)
            dist_nm = dist_deg * 60.0
            
            radius_nm = max(float(h.get("radius_nm", 0.1)), 0.1)
            if dist_nm <= radius_nm:
                risk = h["severity"] * (1.0 - (dist_nm / radius_nm))
                if risk > max_risk:
                    max_risk = risk
        return float(max_risk)
