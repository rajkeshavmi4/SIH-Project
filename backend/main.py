from datetime import date
import os

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.iceberg_service import IcebergService
from backend.risk_engine import RiskEngine
from backend.route_engine import RouteEngine
from backend.sea_ice_ml import SeaIceMLService
from backend.sea_ice_service import SeaIceService

app = FastAPI(title="PolarRoute AI", version="1.0.0")

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
risk_engine = RiskEngine(sea_ice_service, iceberg_service, sea_ice_ml)
route_engine = RouteEngine(risk_engine)


class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    dest_lat: float
    dest_lon: float
    departure_date: str
    vessel_type: str


class SeaIceRequest(BaseModel):
    forecast_date: str


@app.get("/api/environment/layers")
def get_environment_layers():
    """Returns deterministic Antarctic sea-ice zones and iceberg tracking vectors."""
    return {
        "ice_zones": sea_ice_service.get_geojson_zones(),
        "icebergs": iceberg_service.get_all_icebergs(),
        "data_notice": "Deterministic Polar Simulation Model (Prototype Dataset)"
    }


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
    return route_engine.compute_all_routes(
        start=(req.start_lat, req.start_lon),
        end=(req.dest_lat, req.dest_lon),
        vessel_type=req.vessel_type
    )


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return f.read()