import os
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.iceberg_service import IcebergService
from backend.iceberg_ml_service import IcebergMLService
from backend.live_data_service import LiveEnvironmentService
from backend.risk_engine import RiskEngine
from backend.route_engine import RouteEngine
from backend.sea_ice_ml import SeaIceMLService
from backend.sea_ice_service import SeaIceService

app = FastAPI(title="IndraSetu : SIH Antarctic Decision Support System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sea_ice_service = SeaIceService()
sea_ice_ml = SeaIceMLService()
iceberg_service = IcebergService()
iceberg_ml_service = IcebergMLService()
live_env_service = LiveEnvironmentService()

risk_engine = RiskEngine(sea_ice_service, iceberg_service, sea_ice_ml, live_env_srv=live_env_service)
route_engine = RouteEngine(risk_engine)


class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    dest_lat: float
    dest_lon: float
    departure_date: str
    vessel_type: str


class EnRouteRerouteRequest(BaseModel):
    current_lat: float
    current_lon: float
    dest_lat: float
    dest_lon: float
    vessel_type: str = "Polar Class 4"
    active_profile: str = "Safest"
    traveled_waypoints: Optional[List[List[float]]] = None


class RouteEvaluationRequest(BaseModel):
    waypoints: List[List[float]]
    vessel_type: str = "Polar Class 4"
    profile_name: str = "Safest"
    departure_date: Optional[str] = None


class DynamicHazardRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    hazard_type: str = Field("Drifting Iceberg", min_length=1, max_length=80)
    radius_nm: float = Field(20.0, gt=0.0, le=500.0)
    severity: float = Field(0.95, ge=0.0, le=1.0)
    description: str = Field("", max_length=500)


class SeaIceRequest(BaseModel):
    forecast_date: str


@app.get("/api/environment/layers")
def get_environment_layers():
    """Returns sea ice and ML-predicted iceberg trajectories from real tracked data."""
    featured_icebergs = iceberg_ml_service.get_featured_icebergs()
    return {
        "ice_zones": sea_ice_service.get_geojson_zones(),
        "icebergs": featured_icebergs,
        "dynamic_hazards": live_env_service.get_active_hazards(),
        "data_notice": "Iceberg trajectories from trained GRU model on real historical tracking data (last observed date shown per iceberg)",
        "iceberg_summary": {
            "modeled_tracks": len(iceberg_ml_service.iceberg_ids),
            "featured_tracks": len(featured_icebergs),
            "risk_tracks": len(iceberg_service.get_all_icebergs()),
            "forecast_date": iceberg_service.forecast_date,
            "region": "Antarctic maritime corridor: 50S-82S, 180W-180E",
            "data_status": "Historical tracks plus GRU forecast artifact; no live iceberg feed connected"
        },
        "system_status": {
            "route_engine": "Risk-weighted spherical A*",
            "sea_ice_model": "ConvLSTM forecast + satellite observations",
            "iceberg_model": "GRU 24/48/72-hour drift forecast",
            "weather_source": "Open-Meteo when reachable; deterministic polar edge fallback otherwise"
        }
    }


@app.get("/api/sea-ice/heatmap")
def get_sea_ice_heatmap(date: Optional[str] = Query(None), stride: int = Query(3, ge=1)):
    """Returns real satellite observation raster points for Antarctic sea-ice heatmap rendering."""
    return sea_ice_service.get_real_satellite_heatmap(date_str=date, stride=stride)


@app.get("/api/live/environmental-data")
def get_live_environmental_data(lat: float = Query(-65.0), lon: float = Query(-55.0)):
    """Pulls multi-variable live MetOcean parameters (Wind, Wave, Vis, Temp) + risk metrics."""
    metocean = live_env_service.fetch_live_metocean(lat, lon)
    risk_data = risk_engine.calculate_cell_risk(lat, lon)
    return {
        "coordinates": [lat, lon],
        "metocean": metocean,
        "risk_breakdown": risk_data
    }


@app.post("/api/live/hazard/trigger")
def trigger_dynamic_hazard(req: DynamicHazardRequest):
    """Injects a dynamic hazard (e.g. drifting iceberg or sudden ice field) during active voyage."""
    hazard = live_env_service.inject_dynamic_hazard(
        lat=req.lat,
        lon=req.lon,
        hazard_type=req.hazard_type,
        radius_nm=req.radius_nm,
        severity=req.severity,
        description=req.description
    )
    return {"status": "success", "hazard": hazard}


@app.post("/api/sea-ice/forecast")
def forecast_sea_ice(req: SeaIceRequest):
    prediction = sea_ice_ml.forecast(req.forecast_date)
    return {
        "date": req.forecast_date,
        "resolution": "128x128",
        "min": float(np.nanmin(prediction)),
        "max": float(np.nanmax(prediction)),
        "mean": float(np.nanmean(prediction)),
    }


@app.post("/api/routes/calculate")
def calculate_routes(req: RouteRequest):
    result = route_engine.compute_all_routes(
        start=(req.start_lat, req.start_lon),
        end=(req.dest_lat, req.dest_lon),
        vessel_type=req.vessel_type,
        departure_date=req.departure_date
    )
    result["provenance"] = {
        "route_engine": "Risk-weighted spherical A*",
        "risk_engine": "ConvLSTM sea-ice + GRU iceberg drift + MetOcean + dynamic hazards",
        "operating_mode": "Local ML inference; live weather is optional"
    }
    return result


@app.post("/api/routes/reroute")
def reroute_en_route(req: EnRouteRerouteRequest):
    """Dynamic 1-minute / en-route path optimization while vessel is actively traveling."""
    return route_engine.compute_reroute_en_route(
        current_pos=(req.current_lat, req.current_lon),
        dest_pos=(req.dest_lat, req.dest_lon),
        vessel_type=req.vessel_type,
        active_profile=req.active_profile,
        traveled_waypoints=req.traveled_waypoints
    )


@app.post("/api/routes/evaluate")
def evaluate_route(req: RouteEvaluationRequest):
    """Multi-criteria voyage performance indexing, CO2 footprint, and hull stress evaluation."""
    return route_engine.evaluate_route(
        waypoints=req.waypoints,
        vessel_type=req.vessel_type,
        profile_name=req.profile_name,
        departure_date=req.departure_date
    )


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return f.read()