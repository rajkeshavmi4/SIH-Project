from pathlib import Path
import numpy as np
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent

class SeaIceService:
    """
    High-Performance Antarctic Sea-Ice Service.
    Loads real satellite observation datasets (sic.npy, lat.npy, lon.npy)
    to generate authentic sea-ice concentration heatmaps and risk profiles.
    """
    
    def __init__(self):
        project_root = ROOT_DIR
        self.sic_path = project_root / "Sea ice prediction" / "data" / "processed" / "sic.npy"
        self.dates_path = project_root / "Sea ice prediction" / "data" / "processed" / "dates.npy"
        self.lat_path = project_root / "Sea ice prediction" / "data" / "processed" / "lat.npy"
        self.lon_path = project_root / "Sea ice prediction" / "data" / "processed" / "lon.npy"
        
        self.has_real_dataset = (
            self.sic_path.exists() and 
            self.lat_path.exists() and 
            self.lon_path.exists()
        )

        if self.has_real_dataset:
            self.sic_data = np.load(self.sic_path, mmap_mode="r")
            self.dates = np.load(self.dates_path) if self.dates_path.exists() else None
            self.lat_grid = np.load(self.lat_path)
            self.lon_grid = np.load(self.lon_path)
            print(f"[SATELLITE SERVICE] Loaded real satellite dataset: {self.sic_data.shape[0]} observations, grid {self.lat_grid.shape}")
        else:
            self.sic_data = None
            self.lat_grid = None
            self.lon_grid = None

    def get_ice_concentration(self, lat: float, lon: float) -> float:
        """Returns sea ice concentration between 0.0 (open water) and 1.0 (pack ice)."""
        if self.has_real_dataset:
            dist = (self.lat_grid - lat)**2 + (self.lon_grid - lon)**2
            idx = np.unravel_index(np.argmin(dist), dist.shape)
            latest_frame = np.nan_to_num(self.sic_data[-1], nan=0.0)
            return float(np.clip(latest_frame[idx], 0.0, 1.0))
        
        base = np.clip((-55.0 - lat) / 25.0, 0.0, 1.0)
        weddell_factor = 0.25 * np.exp(-((lat - -72.0)**2 / 40.0 + (lon - -45.0)**2 / 600.0))
        ross_factor = 0.20 * np.exp(-((lat - -75.0)**2 / 40.0 + (lon - 175.0)**2 / 600.0))
        return float(np.clip(base * 0.75 + weddell_factor + ross_factor, 0.0, 1.0))

    def get_real_satellite_heatmap(self, date_str: Optional[str] = None, stride: int = 3) -> Dict[str, Any]:
        """
        Extracts accurate spatial grid of sea-ice concentration directly from real satellite observation rasters.
        """
        if not self.has_real_dataset:
            return self._fallback_heatmap(stride=stride)

        frame_idx = -1
        obs_date = "Latest Observation"
        if date_str and self.dates is not None:
            try:
                target_dt = np.datetime64(date_str, "D")
                deltas = np.abs(self.dates.astype("datetime64[D]") - target_dt)
                frame_idx = int(np.argmin(deltas))
                obs_date = str(self.dates[frame_idx])[:10]
            except Exception:
                pass
        elif self.dates is not None:
            obs_date = str(self.dates[-1])[:10]

        frame = np.nan_to_num(self.sic_data[frame_idx], nan=0.0)
        
        sub_lat = self.lat_grid[::stride, ::stride]
        sub_lon = self.lon_grid[::stride, ::stride]
        sub_frame = frame[::stride, ::stride]

        mask = (sub_frame > 0.05) & ~np.isnan(sub_lat) & ~np.isnan(sub_lon) & (sub_lat < -50.0)
        
        valid_lats = sub_lat[mask]
        valid_lons = sub_lon[mask]
        valid_sics = sub_frame[mask]

        points = []
        for la, lo, val in zip(valid_lats, valid_lons, valid_sics):
            points.append([round(float(la), 3), round(float(lo), 3), round(float(val), 3)])

        mean_conc = round(float(np.mean(valid_sics)) if len(valid_sics) > 0 else 0.0, 3)
        max_conc = round(float(np.max(valid_sics)) if len(valid_sics) > 0 else 0.0, 3)
        ice_extent_sqkm = round(float(np.sum(valid_sics > 0.15) * 625.0 * (stride * stride)), 0)

        return {
            "source": "NOAA/NSIDC Passive Microwave Satellite Observation Dataset",
            "observation_date": obs_date,
            "total_points": len(points),
            "points": points,
            "min_conc": 0.05,
            "max_conc": max_conc,
            "mean_conc": mean_conc,
            "ice_extent_sqkm": ice_extent_sqkm
        }

    def _fallback_heatmap(self, stride: int = 3) -> Dict[str, Any]:
        points = []
        step_lat = 1.5
        step_lon = 3.0
        lats = np.arange(-82.0, -55.0 + step_lat, step_lat)
        lons = np.arange(-180.0, 180.0 + step_lon, step_lon)
        all_concs = []
        for lat in lats:
            for lon in lons:
                conc = round(self.get_ice_concentration(float(lat), float(lon)), 3)
                if conc > 0.05:
                    points.append([round(float(lat), 2), round(float(lon), 2), conc])
                    all_concs.append(conc)
        arr = np.array(all_concs) if all_concs else np.array([0.0])
        return {
            "source": "Deterministic Synthetic Polar Model",
            "observation_date": "Simulated",
            "total_points": len(points),
            "points": points,
            "min_conc": 0.05,
            "max_conc": float(np.max(arr)),
            "mean_conc": round(float(np.mean(arr)), 3),
            "ice_extent_sqkm": 14200000.0
        }

    def get_geojson_zones(self):
        """Returns low, medium, and high ice concentration polygon zones for map overlay."""
        zones = []
        demo_zones = [
            {"name": "Weddell Sea Pack Ice Sector", "coords": [[-65, -60], [-74, -60], [-75, -25], [-66, -25]], "risk": 0.85, "type": "High Risk Corridor"},
            {"name": "Ross Ice Shelf Sector", "coords": [[-71, 160], [-78, 160], [-78, -160], [-71, -160]], "risk": 0.78, "type": "High Risk Corridor"},
            {"name": "Amundsen Sea Marginal Sector", "coords": [[-68, -120], [-74, -120], [-74, -90], [-68, -90]], "risk": 0.60, "type": "Medium Risk Corridor"},
            {"name": "Davis Sea Ice Shelf Sector", "coords": [[-62, 75], [-68, 75], [-68, 100], [-62, 100]], "risk": 0.40, "type": "Low Risk Corridor"}
        ]
        for z in demo_zones:
            poly = [[lon, lat] for lat, lon in z["coords"]]
            poly.append(poly[0])
            zones.append({
                "type": "Feature",
                "properties": {"name": z["name"], "risk": z["risk"], "type": z["type"]},
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": zones}