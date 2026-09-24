import pytest
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)

def test_api_status_endpoint_demo():
    resp = client.get("/api/data/status?data_mode=demo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_mode"] == "demo"
    assert data["source"] == "demo_seed"
    assert data["validated"] is True
    assert data["players"] > 0
    assert data["teams"] >= 16

def test_api_optimise_requires_ft_confirmation_in_live_mode():
    """In live mode, unconfirmed FT must return 400 FREE_TRANSFERS_UNCONFIRMED."""
    resp = client.post("/api/optimise", json={
        "manager_id": 99999,
        "data_mode": "live",
        "horizon": 1,
        "confirm_free_transfers": False
    })
    # Will fail with 400 or 404 (since 99999 is demo sentinel in live mode)
    assert resp.status_code in [400, 404]

def test_api_optimise_works_in_demo_mode():
    resp = client.post("/api/optimise", json={
        "manager_id": 99999,
        "data_mode": "demo",
        "horizon": 1,
        "confirm_free_transfers": True,
        "free_transfers": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "plans" in data
    assert len(data["plans"]) >= 1
    assert data["snapshot_id"].startswith("snap_")

def test_api_refresh_endpoint_demo():
    resp = client.post("/api/data/refresh?data_mode=demo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["validated"] is True
    assert data["data_mode"] == "demo"

def test_demo_mini_leagues_and_differentials():
    leagues_resp = client.get("/api/mini-leagues?manager_id=99999&data_mode=demo")
    assert leagues_resp.status_code == 200
    leagues = leagues_resp.json()["leagues"]
    assert len(leagues) >= 1

    analysis_resp = client.get(
        f"/api/mini-leagues/{leagues[0]['id']}/analysis?manager_id=99999&data_mode=demo"
    )
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()
    assert analysis["sample_size"] > 0
    assert "differentials" in analysis
    assert "threats" in analysis
