"""API tests for health, prediction, recommendation endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def sample_payload() -> dict[str, float | str]:
    return {
        "address": "123 Main St, San Jose, CA",
        "list_price": 850000,
        "beds": 3,
        "baths": 2,
        "sqft": 1500,
        "neighborhood_price_per_sqft": 550,
    }


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_data_freshness_endpoint() -> None:
    response = client.get("/data/freshness")
    body = response.json()

    assert response.status_code == 200
    assert "label" in body
    assert body["retention_policy"] == "append-only"


def test_dashboard_support_endpoints() -> None:
    endpoints = [
        "/models/evaluation",
        "/data/coverage",
        "/analytics/market",
        "/predictions/audit",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.json()


def test_predict_endpoint() -> None:
    response = client.post("/predict", json=sample_payload())
    body = response.json()

    assert response.status_code == 200
    assert body["address"] == "123 Main St, San Jose, CA"
    assert "investment_score" in body
    assert "market_signal_score" in body
    assert "recommendation_label" in body
    assert "buy_decision" in body
    assert "rent_decision" in body
    assert "sell_decision" in body


def test_recommend_endpoint() -> None:
    response = client.post("/recommend", json=sample_payload())
    body = response.json()

    assert response.status_code == 200
    assert body["recommendation_label"] in {
        "strong buy",
        "buy with caution",
        "hold/monitor",
        "avoid",
    }


def test_predict_validation_failure() -> None:
    bad_payload = sample_payload()
    bad_payload["sqft"] = 0

    response = client.post("/predict", json=bad_payload)
    assert response.status_code == 422
