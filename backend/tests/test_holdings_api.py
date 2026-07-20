"""End-to-end coverage of /api/holdings: create-with-inline-instrument,
de-dup on re-add via isin/ticker, update, delete, 404s."""

from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app)


def test_create_holding_with_inline_instrument():
    client = _client_with_fresh_db()
    try:
        resp = client.post(
            "/api/holdings",
            json={
                "instrument": {
                    "isin": "IE00BK5BQT80",
                    "ticker": "VWCE.DE",
                    "name": "Vanguard FTSE All-World UCITS ETF",
                    "currency": "EUR",
                },
                "quantity": 10,
                "avg_cost_price": 95.5,
                "cost_currency": "EUR",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["instrument"]["ticker"] == "VWCE.DE"
        assert body["quantity"] == 10

        resp = client.get("/api/holdings")
        assert len(resp.json()) == 1
        resp = client.get("/api/instruments")
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_create_holding_reuses_existing_instrument_by_isin():
    client = _client_with_fresh_db()
    try:
        payload = {
            "instrument": {
                "isin": "IE00B4L5Y983",
                "name": "iShares Core MSCI World",
                "currency": "EUR",
            },
            "quantity": 5,
            "avg_cost_price": 70.0,
            "cost_currency": "EUR",
        }
        first = client.post("/api/holdings", json=payload).json()
        second = client.post("/api/holdings", json=payload).json()

        assert first["instrument"]["id"] == second["instrument"]["id"]
        assert len(client.get("/api/instruments").json()) == 1
        assert len(client.get("/api/holdings").json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_create_holding_requires_instrument_id_or_full_spec():
    client = _client_with_fresh_db()
    try:
        resp = client.post(
            "/api/holdings",
            json={
                "instrument": {"name": "Missing ticker/isin", "currency": "EUR"},
                "quantity": 1,
                "avg_cost_price": 1,
                "cost_currency": "EUR",
            },
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_update_and_delete_holding():
    client = _client_with_fresh_db()
    try:
        created = client.post(
            "/api/holdings",
            json={
                "instrument": {"ticker": "AAPL", "name": "Apple", "currency": "USD"},
                "quantity": 2,
                "avg_cost_price": 150.0,
                "cost_currency": "USD",
            },
        ).json()
        holding_id = created["id"]

        resp = client.put(f"/api/holdings/{holding_id}", json={"quantity": 3})
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 3

        resp = client.delete(f"/api/holdings/{holding_id}")
        assert resp.status_code == 204

        resp = client.get("/api/holdings")
        assert resp.json() == []

        resp = client.delete(f"/api/holdings/{holding_id}")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
