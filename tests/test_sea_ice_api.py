from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_sea_ice_forecast_endpoint_exists():
    response = client.post(
        "/api/sea-ice/forecast",
        json={"forecast_date": "2024-11-13"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2024-11-13"
    assert payload["resolution"] == "128x128"
    assert "min" in payload and "max" in payload and "mean" in payload
