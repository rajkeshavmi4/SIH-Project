import unittest
from starlette.testclient import TestClient
from backend.main import app
from backend.live_data_service import LiveEnvironmentService
from backend.risk_engine import RiskEngine
from backend.route_engine import RouteEngine
from backend.sea_ice_service import SeaIceService
from backend.iceberg_service import IcebergService

class TestDynamicReroutingSystem(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_live_environment_service(self):
        service = LiveEnvironmentService()
        metocean = service.fetch_live_metocean(-65.0, -55.0)
        self.assertIn("wind_speed_knots", metocean)
        self.assertIn("wave_height_m", metocean)
        self.assertIn("air_temperature_c", metocean)
        self.assertIn("visibility_km", metocean)

    def test_iceberg_trajectory_horizons_are_absolute(self):
        service = IcebergService()
        iceberg = service.get_all_icebergs()[0]
        trajectory = iceberg["trajectory"]

        self.assertEqual(len(trajectory), 4)
        first_horizon_lat = trajectory[1][1] - trajectory[0][1]
        second_horizon_lat = trajectory[2][1] - trajectory[0][1]
        third_horizon_lat = trajectory[3][1] - trajectory[0][1]

        self.assertAlmostEqual(second_horizon_lat, first_horizon_lat * 2, places=2)
        self.assertAlmostEqual(third_horizon_lat, first_horizon_lat * 3, places=2)

    def test_dynamic_hazard_injection(self):
        service = LiveEnvironmentService()
        hazard = service.inject_dynamic_hazard(
            lat=-66.0, lon=-58.0, hazard_type="Tabular Iceberg", radius_nm=30.0, severity=0.9
        )
        self.assertEqual(hazard["hazard_type"], "Tabular Iceberg")
        risk_at = service.get_dynamic_hazard_risk_at(-66.0, -58.0)
        self.assertGreater(risk_at, 0.8)

    def test_en_route_rerouting(self):
        sea_ice_srv = SeaIceService()
        berg_srv = IcebergService()
        live_env = LiveEnvironmentService()
        risk_eng = RiskEngine(sea_ice_srv, berg_srv, live_env_srv=live_env)
        route_eng = RouteEngine(risk_eng)

        reroute = route_eng.compute_reroute_en_route(
            current_pos=(-65.0, -60.0),
            dest_pos=(-64.8, -64.1),
            vessel_type="Polar Class 4",
            active_profile="Safest"
        )
        self.assertTrue(reroute["reroute_triggered"])
        self.assertGreater(len(reroute["remaining_waypoints"]), 0)
        self.assertGreater(reroute["remaining_distance_nm"], 0)

    def test_route_evaluation_matrix(self):
        sea_ice_srv = SeaIceService()
        berg_srv = IcebergService()
        live_env = LiveEnvironmentService()
        risk_eng = RiskEngine(sea_ice_srv, berg_srv, live_env_srv=live_env)
        route_eng = RouteEngine(risk_eng)

        eval_res = route_eng.evaluate_route(
            waypoints=[[-65.0, -60.0], [-66.0, -62.0], [-64.8, -64.1]],
            vessel_type="Polar Class 4",
            profile_name="Safest"
        )
        self.assertIn("voyage_performance_index", eval_res)
        self.assertIn("co2_emissions_mt", eval_res)
        self.assertIn("hull_stress_index", eval_res)

    def test_api_live_environmental_data(self):
        response = self.client.get("/api/live/environmental-data?lat=-65.0&lon=-55.0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("metocean", data)
        self.assertIn("risk_breakdown", data)

    def test_api_routes_reroute_endpoint(self):
        payload = {
            "current_lat": -65.0,
            "current_lon": -60.0,
            "dest_lat": -64.8,
            "dest_lon": -64.1,
            "vessel_type": "Polar Class 4",
            "active_profile": "Safest"
        }
        response = self.client.post("/api/routes/reroute", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["reroute_triggered"])

    def test_api_route_evaluation_endpoint(self):
        payload = {
            "waypoints": [[-65.0, -60.0], [-66.0, -62.0], [-64.8, -64.1]],
            "vessel_type": "Polar Class 4",
            "profile_name": "Safest"
        }
        response = self.client.post("/api/routes/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("voyage_performance_index", data)

    def test_api_hazard_trigger_endpoint(self):
        payload = {
            "lat": -65.5,
            "lon": -59.0,
            "hazard_type": "Drifting Iceberg A-76",
            "radius_nm": 20.0,
            "severity": 0.95,
            "description": "Test hazard injection"
        }
        response = self.client.post("/api/live/hazard/trigger", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

if __name__ == "__main__":
    unittest.main()
