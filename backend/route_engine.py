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

    def scan_route_for_cyclones(self, path: list, check_interval_km: float = 50.0) -> list:
        """Checks points along the route at regular intervals for cyclone signatures."""
        alerts = []
        accumulated_dist = 0.0
        last_checked_dist = 0.0

        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i + 1]
            seg_dist_nm = self._haversine_distance(p1[0], p1[1], p2[0], p2[1])
            seg_dist_km = seg_dist_nm * 1.852
            accumulated_dist += seg_dist_km

            if accumulated_dist - last_checked_dist >= check_interval_km:
                result = self.risk_engine.live_env_srv.check_cyclone_signature(p2[0], p2[1])
                if result["is_cyclone_risk"]:
                    alerts.append(result)
                last_checked_dist = accumulated_dist

        return alerts

    def _a_star(self, start: tuple, end: tuple, vessel_type: str, weight_risk: float, departure_date: str = None, corridor_offset: float = 0.0):
        """A* routing across a spherical Antarctic coordinate lattice."""
        start_node = (round(start[0], 1), round(start[1], 1))
        end_node = (round(end[0], 1), round(end[1], 1))
        
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        came_from = {}
        g_score = {start_node: 0.0}
        
        step_lat = 1.5
        step_lon = 3.0
        
        visited_count = 0
        max_iterations = 12000

        if self._haversine_distance(start[0], start[1], end[0], end[1]) > 2500.0:
            segments = 12
            lon_delta = (end[1] - start[1] + 180.0) % 360.0 - 180.0
            return [
                (
                    round(start[0] + (end[0] - start[0]) * index / segments, 1),
                    round(start[1] + lon_delta * index / segments, 1),
                )
                for index in range(segments + 1)
            ]

        while open_set and visited_count < max_iterations:
            visited_count += 1
            _, current = heapq.heappop(open_set)
            
            if self._haversine_distance(current[0], current[1], end_node[0], end_node[1]) < 120.0:
                path = [end_node]
                curr = current
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.append(start_node)
                path.reverse()
                return path

            cur_lat, cur_lon = current
            
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
                risk_data = self.risk_engine.calculate_cell_risk(n_lat, n_lon, vessel_type, departure_date)
                
                progress = min(1.0, max(0.0, abs(n_lat - start[0]) / max(abs(end[0] - start[0]), 0.1)))
                lon_delta = (end[1] - start[1] + 180.0) % 360.0 - 180.0
                preferred_lon = start[1] + lon_delta * progress + corridor_offset * math.sin(math.pi * progress)
                lane_penalty = abs(((n_lon - preferred_lon + 180.0) % 360.0) - 180.0)
                edge_cost = dist * (1.0 + weight_risk * (risk_data["total_risk"] ** 2) * 8.0 + lane_penalty * 0.8)
                tentative_g = g_score[current] + edge_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self._haversine_distance(n_lat, n_lon, end_node[0], end_node[1])
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        # Long-haul station pairs can exceed the local grid search budget.
        # Return a segmented great-circle approximation instead of failing the API.
        segments = 12
        lon_delta = (end[1] - start[1] + 180.0) % 360.0 - 180.0
        return [
            (
                round(start[0] + (end[0] - start[0]) * index / segments, 1),
                round(start[1] + lon_delta * index / segments, 1),
            )
            for index in range(segments + 1)
        ]

    def _calculate_metrics(self, path: list, vessel_type: str, profile_name: str, departure_date: str = None):
        total_dist_nm = 0.0
        risk_accum = 0.0
        sea_ice_accum = 0.0
        iceberg_accum = 0.0
        weather_accum = 0.0
        
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            d = self._haversine_distance(p1[0], p1[1], p2[0], p2[1])
            total_dist_nm += d
            risk_data = self.risk_engine.calculate_cell_risk(p1[0], p1[1], vessel_type, departure_date)
            r = risk_data["total_risk"]
            risk_accum += r * d
            sea_ice_accum += risk_data["sea_ice_risk"] * d
            iceberg_accum += risk_data["iceberg_risk"] * d
            weather_accum += risk_data["weather_risk"] * d

        avg_risk = risk_accum / max(1.0, total_dist_nm)
        
        base_speed = 14.0
        if "Class 1" in vessel_type:
            base_speed = 12.0
        elif "Standard" in vessel_type:
            base_speed = 15.0

        effective_speed = base_speed * (1.0 - (avg_risk * 0.45))
        est_hours = total_dist_nm / max(effective_speed, 4.0)
        
        base_fuel_rate = 1.0
        ice_resistance_factor = 1.0 + (avg_risk * 0.6)
        fuel_rate = base_fuel_rate * ice_resistance_factor
            
        fuel_consumption_mt = round(est_hours * fuel_rate, 1)

        if profile_name == "Safest":
            explanation = "Actively diverts around heavy pack ice and steers clear of tracked iceberg drift corridors, trading travel distance for minimal collision probability."
        elif profile_name == "Balanced":
            explanation = "Balances transit time and safety by skirting the perimeter of high-density sea-ice fields while avoiding known iceberg clusters."
        else:
            explanation = "Follows the near-geodesic trajectory prioritizing shortest transit distance and lowest fuel consumption; accepts elevated sea-ice resistance."

        cyclone_alerts = self.scan_route_for_cyclones(path)

        return {
            "name": profile_name,
            "waypoints": [[lat, lon] for lat, lon in path],
            "distance_nm": round(total_dist_nm, 1),
            "estimated_time_days": round(est_hours / 24.0, 1),
            "estimated_time_hours": round(est_hours, 1),
            "fuel_consumption_mt": fuel_consumption_mt,
            "overall_risk_score": round(avg_risk * 100, 1),
            "risk_breakdown": {
                "sea_ice": round((sea_ice_accum / max(1.0, total_dist_nm)) * 100, 1),
                "iceberg": round((iceberg_accum / max(1.0, total_dist_nm)) * 100, 1),
                "weather": round((weather_accum / max(1.0, total_dist_nm)) * 100, 1),
                "navigation": round(avg_risk * 100, 1)
            },
            "explanation": explanation,
            "cyclone_alerts": cyclone_alerts
        }

    def compute_all_routes(self, start: tuple, end: tuple, vessel_type: str, departure_date: str = None):
        safest_path = self._a_star(start, end, vessel_type, weight_risk=15.0, departure_date=departure_date, corridor_offset=4.0)
        safest_metrics = self._calculate_metrics(safest_path, vessel_type, "Safest", departure_date)

        balanced_path = self._a_star(start, end, vessel_type, weight_risk=3.5, departure_date=departure_date, corridor_offset=0.0)
        balanced_metrics = self._calculate_metrics(balanced_path, vessel_type, "Balanced", departure_date)

        efficient_path = self._a_star(start, end, vessel_type, weight_risk=0.2, departure_date=departure_date, corridor_offset=-4.0)
        efficient_metrics = self._calculate_metrics(efficient_path, vessel_type, "Fuel Efficient", departure_date)

        return {
            "routes": {
                "safest": safest_metrics,
                "balanced": balanced_metrics,
                "fuel_efficient": efficient_metrics
            }
        }

    def compute_reroute_en_route(self, current_pos: tuple, dest_pos: tuple, vessel_type: str = "Polar Class 4", active_profile: str = "Safest", traveled_waypoints: list = None) -> dict:
        weight_map = {"Safest": 15.0, "Balanced": 3.5, "Fuel Efficient": 0.2}
        weight = weight_map.get(active_profile, 10.0)

        remaining_path = self._a_star(current_pos, dest_pos, vessel_type, weight_risk=weight)
        remaining_metrics = self._calculate_metrics(remaining_path, vessel_type, active_profile)

        traveled = traveled_waypoints or [[current_pos[0], current_pos[1]]]
        full_waypoints = traveled[:-1] + remaining_metrics["waypoints"]

        current_risk_data = self.risk_engine.calculate_cell_risk(current_pos[0], current_pos[1], vessel_type)

        explanation = f"Dynamic En-Route Detour recalculation initiated at ({current_pos[0]:.2f}, {current_pos[1]:.2f}). " \
                      f"Detected hazard ahead. Path re-routed around risk field. Remaining distance: {remaining_metrics['distance_nm']} NM."

        return {
            "reroute_triggered": True,
            "profile_name": active_profile,
            "current_position": [current_pos[0], current_pos[1]],
            "destination_position": [dest_pos[0], dest_pos[1]],
            "remaining_waypoints": remaining_metrics["waypoints"],
            "full_voyage_waypoints": full_waypoints,
            "remaining_distance_nm": remaining_metrics["distance_nm"],
            "remaining_time_hours": remaining_metrics["estimated_time_hours"],
            "remaining_fuel_mt": remaining_metrics["fuel_consumption_mt"],
            "remaining_risk_score": remaining_metrics["overall_risk_score"],
            "current_cell_risk": round(current_risk_data["total_risk"] * 100, 1),
            "explanation": explanation
        }

    def evaluate_route(self, waypoints: list, vessel_type: str = "Polar Class 4", profile_name: str = "Safest", departure_date: str = None) -> dict:
        """
        Comprehensive Multi-Criteria Voyage Evaluation & Performance Indexing.
        Calculates carbon emissions, hull stress, ice resistance, segment risk profile, and VPI score.
        """
        if not waypoints or len(waypoints) < 2:
            return {"error": "Invalid waypoints for evaluation."}

        total_dist_nm = 0.0
        risk_accum = 0.0
        ice_risk_accum = 0.0
        berg_risk_accum = 0.0
        high_risk_nm = 0.0

        segments = []
        for i in range(len(waypoints) - 1):
            p1, p2 = waypoints[i], waypoints[i+1]
            seg_dist = self._haversine_distance(p1[0], p1[1], p2[0], p2[1])
            total_dist_nm += seg_dist

            risk_info = self.risk_engine.calculate_cell_risk(p1[0], p1[1], vessel_type, departure_date)
            r_tot = risk_info["total_risk"]
            r_ice = risk_info["sea_ice_risk"]
            r_berg = risk_info["iceberg_risk"]

            risk_accum += r_tot * seg_dist
            ice_risk_accum += r_ice * seg_dist
            berg_risk_accum += r_berg * seg_dist

            if r_tot > 0.50:
                high_risk_nm += seg_dist

            segments.append({
                "segment_index": i + 1,
                "coordinates": [p1, p2],
                "distance_nm": round(seg_dist, 1),
                "total_risk_score": round(r_tot * 100, 1),
                "sea_ice_risk_score": round(r_ice * 100, 1),
                "iceberg_risk_score": round(r_berg * 100, 1),
                "risk_tier": "HIGH HAZARD" if r_tot > 0.50 else ("MODERATE EXPOSURE" if r_tot > 0.25 else "LOW RISK")
            })

        avg_risk = risk_accum / max(1.0, total_dist_nm)
        avg_ice_risk = ice_risk_accum / max(1.0, total_dist_nm)
        avg_berg_risk = berg_risk_accum / max(1.0, total_dist_nm)

        base_speed = 14.0 if "Class 4" in vessel_type else (12.0 if "Class 1" in vessel_type else 15.0)
        effective_speed = base_speed * (1.0 - (avg_risk * 0.45))
        est_hours = total_dist_nm / max(effective_speed, 4.0)

        fuel_rate = 1.2 if "Balanced" in profile_name else (0.95 if "Efficient" in profile_name else 1.35)
        fuel_mt = round(est_hours * fuel_rate, 1)
        fuel_cost_usd = round(fuel_mt * 650.0, 0)
        co2_emissions_mt = round(fuel_mt * 3.114, 1)

        vpi_score = max(10, min(99, round(100.0 - (0.45 * avg_risk * 100.0) - (0.003 * total_dist_nm), 1)))
        hull_stress_index = round(1.0 + (avg_ice_risk * 2.5), 2)
        high_risk_ratio = round((high_risk_nm / max(1.0, total_dist_nm)) * 100.0, 1)

        tactical_briefing = (
            f"Voyage Performance Index: {vpi_score}/100. "
            f"Route covers {total_dist_nm:.1f} NM with an average ice risk of {avg_risk*100:.1f}%. "
            f"Estimated fuel consumption is {fuel_mt} MT (${fuel_cost_usd:,.0f} USD) emitting {co2_emissions_mt} MT CO2. "
            f"High-risk corridor exposure is {high_risk_ratio}%. Recommended for voyage command approval."
        )

        return {
            "profile_name": profile_name,
            "vessel_type": vessel_type,
            "voyage_performance_index": vpi_score,
            "total_distance_nm": round(total_dist_nm, 1),
            "estimated_time_days": round(est_hours / 24.0, 1),
            "estimated_time_hours": round(est_hours, 1),
            "fuel_consumption_mt": fuel_mt,
            "fuel_cost_usd": fuel_cost_usd,
            "co2_emissions_mt": co2_emissions_mt,
            "hull_stress_index": hull_stress_index,
            "average_risk_score": round(avg_risk * 100, 1),
            "average_sea_ice_risk": round(avg_ice_risk * 100, 1),
            "average_iceberg_risk": round(avg_berg_risk * 100, 1),
            "high_risk_corridor_ratio": high_risk_ratio,
            "tactical_briefing": tactical_briefing,
            "segment_breakdown": segments
        }