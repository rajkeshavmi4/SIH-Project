import math

class IcebergService:
    """Manages iceberg tracking & trajectory drift vectors."""
    
    def __init__(self):
        # Realistic Antarctic tracked icebergs
        self.icebergs = [
            {"id": "A-23A-sub", "lat": -63.2, "lon": -52.0, "size_km2": 3800, "drift_dir": 35, "speed_knots": 1.4},
            {"id": "B-15Y", "lat": -67.5, "lon": -140.2, "size_km2": 450, "drift_dir": 280, "speed_knots": 0.9},
            {"id": "C-19C", "lat": -64.8, "lon": 85.3, "size_km2": 820, "drift_dir": 70, "speed_knots": 1.1},
            {"id": "D-28B", "lat": -70.1, "lon": 15.4, "size_km2": 1200, "drift_dir": 310, "speed_knots": 0.7},
            {"id": "A-76A", "lat": -58.5, "lon": -38.2, "size_km2": 2100, "drift_dir": 45, "speed_knots": 1.8},
            {"id": "IB-902", "lat": -62.0, "lon": -105.0, "size_km2": 150, "drift_dir": 110, "speed_knots": 1.2}
        ]

    def get_all_icebergs(self):
        """Returns iceberg positions and 72-hour forecast trajectory lines."""
        results = []
        for berg in self.icebergs:
            lat = berg["lat"]
            lon = berg["lon"]
            rad = math.radians(berg["drift_dir"])
            
            # Predict 24h, 48h, 72h drift
            drift_coords = [[lon, lat]]
            cur_lat, cur_lon = lat, lon
            for step in [24, 48, 72]:
                dist_deg = (berg["speed_knots"] * step * 1.852) / 111.0
                cur_lat += dist_deg * math.cos(rad)
                cur_lon += (dist_deg * math.sin(rad)) / max(math.cos(math.radians(cur_lat)), 0.1)
                drift_coords.append([round(cur_lon, 3), round(cur_lat, 3)])

            results.append({
                "id": berg["id"],
                "lat": lat,
                "lon": lon,
                "size_km2": berg["size_km2"],
                "speed_knots": berg["speed_knots"],
                "drift_dir": berg["drift_dir"],
                "trajectory": drift_coords
            })
        return results

    def get_iceberg_risk_at(self, lat: float, lon: float) -> float:
        """Proximity penalty for nearby icebergs."""
        min_dist_deg = 999.0
        for berg in self.icebergs:
            dlat = lat - berg["lat"]
            dlon = (lon - berg["lon"]) * math.cos(math.radians(lat))
            dist = math.sqrt(dlat**2 + dlon**2)
            if dist < min_dist_deg:
                min_dist_deg = dist
        
        # High danger within 2.5 degrees (~150 nautical miles)
        if min_dist_deg < 2.5:
            return float(max(0.0, 1.0 - (min_dist_deg / 2.5)))
        return 0.0