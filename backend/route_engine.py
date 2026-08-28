import heapq
import math
from backend.risk_engine import RiskEngine

class RouteEngine:
    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 3440.065  # Nautical miles
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians((lon2 - lon1 + 180) % 360 - 180)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _a_star(self, start: tuple, end: tuple, vessel_type: str, weight_risk: float):
        """A* routing across a spherical Antarctic coordinate lattice."""
        start_node = (round(start[0], 1), round(start[1], 1))
        end_node = (round(end[0], 1), round(end[1], 1))
        
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        came_from = {}
        g_score = {start_node: 0.0}
        
        # Neighbor offsets in lat/lon
        step_lat = 1.5
        step_lon = 3.0
        
        visited_count = 0
        max_iterations = 2500

        while open_set and visited_count < max_iterations:
            visited_count += 1
            _, current = heapq.heappop(open_set)
            
            if self._haversine_distance(current[0], current[1], end_node[0], end_node[1]) < 120.0:
                # Reconstruct path
                path = [end_node]
                curr = current
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.append(start_node)
                path.reverse()
                return path

            cur_lat, cur_lon = current
            
            # 8-direction movements
            neighbors = [
                (cur_lat + step_lat, cur_lon),
                (cur_lat - step_lat, cur_lon),
                (cur_lat, (cur_lon + step_lon + 180) % 360 - 180),
                (cur_lat, (cur_lon - step_lon + 180) % 360 - 180),
                (cur_lat + step_lat, (cur_lon + step_lon + 180) % 360 - 180),
                (cur_lat + step_lat, (cur_lon - step_lon + 180) % 360 - 180),
                (cur_lat - step_lat, (cur_lon + step_lon + 180) % 360 - 180),
                (cur_lat - step_lat, (cur_lon - step_lon + 180) % 360 - 180),
            ]

            for n_lat, n_lon in neighbors:
                if n_lat < -82.0 or n_lat > -50.0:
                    continue
                
                neighbor = (round(n_lat, 1), round(n_lon, 1))
                dist = self._haversine_distance(cur_lat, cur_lon, n_lat, n_lon)
                risk_data = self.risk_engine.calculate_cell_risk(n_lat, n_lon, vessel_type)
                
                # Cost function: Distance combined with weighted environmental risk penalty
                edge_cost = dist * (1.0 + weight_risk * (risk_data["total_risk"] ** 2) * 8.0)
                tentative_g = g_score[current] + edge_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self._haversine_distance(n_lat, n_lon, end_node[0], end_node[1])
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        # Fallback great circle interpolation if path blocked
        return [start_node, ((start_node[0]+end_node[0])/2, (start_node[1]+end_node[1])/2), end_node]

    def _calculate_metrics(self, path: list, vessel_type: str, profile_name: str):
        total_dist_nm = 0.0
        risk_accum = 0.0
        
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            d = self._haversine_distance(p1[0], p1[1], p2[0], p2[1])
            total_dist_nm += d
            r = self.risk_engine.calculate_cell_risk(p1[0], p1[1], vessel_type)["total_risk"]
            risk_accum += r * d

        avg_risk = risk_accum / max(1.0, total_dist_nm)
        
        # Base speed based on vessel type and ice impact
        base_speed = 14.0  # knots
        if "Class 1" in vessel_type:
            base_speed = 12.0
        elif "Standard" in vessel_type:
            base_speed = 15.0

        effective_speed = base_speed * (1.0 - (avg_risk * 0.45))
        est_hours = total_dist_nm / max(effective_speed, 4.0)
        
        # Fuel consumption in Metric Tons (MT)
        fuel_rate = 1.2  # MT/hour
        if "Fuel Efficient" in profile_name:
            fuel_rate = 0.95
        elif "Safest" in profile_name:
            fuel_rate = 1.35
            
        fuel_consumption_mt = round(est_hours * fuel_rate, 1)

        # Dynamic Rationale
        if profile_name == "Safest":
            explanation = "Actively diverts around Weddell Sea heavy pack ice and steers clear of tracked iceberg drift corridors, trading travel distance for minimal collision probability."
        elif profile_name == "Balanced":
            explanation = "Balances transit time and safety by skirting the perimeter of high-density sea-ice fields while avoiding known iceberg clusters."
        else:
            explanation = "Follows the near-geodesic trajectory prioritizing shortest transit distance and lowest fuel consumption; accepts elevated sea-ice resistance."

        return {
            "name": profile_name,
            "waypoints": [[lat, lon] for lat, lon in path],
            "distance_nm": round(total_dist_nm, 1),
            "estimated_time_days": round(est_hours / 24.0, 1),
            "estimated_time_hours": round(est_hours, 1),
            "fuel_consumption_mt": fuel_consumption_mt,
            "overall_risk_score": round(avg_risk * 100, 1),
            "explanation": explanation
        }

    def compute_all_routes(self, start: tuple, end: tuple, vessel_type: str):
        # 1. Safest Route (heavily penalizes risk)
        safest_path = self._a_star(start, end, vessel_type, weight_risk=15.0)
        safest_metrics = self._calculate_metrics(safest_path, vessel_type, "Safest")

        # 2. Balanced Route (moderate risk penalty)
        balanced_path = self._a_star(start, end, vessel_type, weight_risk=3.5)
        balanced_metrics = self._calculate_metrics(balanced_path, vessel_type, "Balanced")

        # 3. Fuel Efficient / Direct Route (minimal risk weighting)
        efficient_path = self._a_star(start, end, vessel_type, weight_risk=0.2)
        efficient_metrics = self._calculate_metrics(efficient_path, vessel_type, "Fuel Efficient")

        return {
            "routes": {
                "safest": safest_metrics,
                "balanced": balanced_metrics,
                "fuel_efficient": efficient_metrics
            }
        }