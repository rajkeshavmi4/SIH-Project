import numpy as np

class SeaIceService:
    """Generates synthetic deterministic Antarctic sea-ice concentration grid."""
    
    def __init__(self, lat_min=-85.0, lat_max=-55.0, lon_min=-180.0, lon_max=180.0, resolution=1.0):
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.res = resolution
        
        self.lats = np.arange(lat_min, lat_max + self.res, self.res)
        self.lons = np.arange(lon_min, lon_max + self.res, self.res)
        
    def get_ice_concentration(self, lat: float, lon: float) -> float:
        """Returns ice concentration between 0.0 (open water) and 1.0 (pack ice)."""
        # Ice concentration increases toward the pole (South)
        base = np.clip((-55.0 - lat) / 25.0, 0.0, 1.0)
        
        # Add deterministic geographic features (e.g., Weddell Sea & Ross Sea ice shelves)
        weddell_factor = 0.25 * np.exp(-((lat - -72.0)**2 / 40.0 + (lon - -45.0)**2 / 600.0))
        ross_factor = 0.20 * np.exp(-((lat - -75.0)**2 / 40.0 + (lon - 175.0)**2 / 600.0))
        
        conc = base * 0.75 + weddell_factor + ross_factor
        return float(np.clip(conc, 0.0, 1.0))

    def get_geojson_zones(self):
        """Returns low, medium, and high ice concentration polygon zones for map overlay."""
        zones = []
        # Synthetic representative zone centers across Antarctica
        demo_zones = [
            {"name": "Weddell Sea Pack Ice", "coords": [[-65, -60], [-74, -60], [-75, -25], [-66, -25]], "risk": 0.85, "type": "High Risk"},
            {"name": "Ross Ice Shelf Zone", "coords": [[-71, 160], [-78, 160], [-78, -160], [-71, -160]], "risk": 0.78, "type": "High Risk"},
            {"name": "Amundsen Sea Drift Zone", "coords": [[-68, -120], [-74, -120], [-74, -90], [-68, -90]], "risk": 0.60, "type": "Medium Risk"},
            {"name": "Davis Sea Marginal Zone", "coords": [[-62, 75], [-68, 75], [-68, 100], [-62, 100]], "risk": 0.40, "type": "Low Risk"}
        ]
        for z in demo_zones:
            poly = [[lon, lat] for lat, lon in z["coords"]]
            poly.append(poly[0])  # Close ring
            zones.append({
                "type": "Feature",
                "properties": {"name": z["name"], "risk": z["risk"], "type": z["type"]},
                "geometry": {"type": "Polygon", "coordinates": [poly]}
            })
        return {"type": "FeatureCollection", "features": zones}