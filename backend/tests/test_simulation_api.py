from fastapi.testclient import TestClient

from app.main import app


def test_montecarlo_endpoint_returns_percentile_bands():
    client = TestClient(app)
    resp = client.post(
        "/api/simulation/montecarlo",
        json={
            "seed_capital": 10000,
            "monthly_contribution": 300,
            "years": 5,
            "expected_annual_return": 0.07,
            "annual_volatility": 0.15,
            "n_paths": 200,
            "random_seed": 42,
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["months"]) == 5 * 12 + 1
    assert len(body["p50"]) == len(body["months"])
    assert body["p5"][-1] <= body["p50"][-1] <= body["p95"][-1]


def test_montecarlo_rejects_invalid_horizon():
    client = TestClient(app)
    resp = client.post(
        "/api/simulation/montecarlo",
        json={
            "seed_capital": 1000,
            "monthly_contribution": 100,
            "years": 0,
            "expected_annual_return": 0.05,
            "annual_volatility": 0.1,
        },
    )
    assert resp.status_code == 422
