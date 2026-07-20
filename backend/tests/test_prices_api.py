"""End-to-end (TestClient) coverage of the /api/prices routes: refresh
persists auto-fetched prices, manual override roundtrips, 404s for
unknown instruments."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.instrument import Instrument
from app.providers import registry
from app.providers.base import PriceQuote
from tests.helpers import FakeAutoProvider


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app), engine


def test_manual_price_override_roundtrip():
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            instrument = Instrument(ticker="ABC", name="Test", currency="EUR")
            s.add(instrument)
            s.commit()
            s.refresh(instrument)
            instrument_id = instrument.id

        resp = client.put(f"/api/prices/{instrument_id}", json={"price": 55.5, "currency": "EUR"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["price"] == 55.5
        assert body["source"] == "manual"

        resp = client.get(f"/api/prices/{instrument_id}")
        assert resp.status_code == 200
        assert resp.json()["price"] == 55.5
    finally:
        app.dependency_overrides.clear()


def test_manual_price_404_for_unknown_instrument():
    client, _ = _client_with_fresh_db()
    try:
        resp = client.put("/api/prices/999", json={"price": 10.0, "currency": "EUR"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_refresh_persists_auto_price_and_reports_fallback_status(monkeypatch):
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            covered = Instrument(ticker="OK", name="Covered", currency="EUR")
            not_covered = Instrument(ticker="NA", name="Not covered", currency="EUR", auto_price_enabled=False)
            s.add_all([covered, not_covered])
            s.commit()
            s.refresh(covered)
            s.refresh(not_covered)
            covered_id, not_covered_id = covered.id, not_covered.id

        quote = PriceQuote(price=200.0, currency="EUR", as_of=datetime.now(timezone.utc))
        monkeypatch.setitem(registry._AUTO_PROVIDERS, "yfinance", FakeAutoProvider(quote))

        resp = client.post("/api/prices/refresh")
        assert resp.status_code == 200
        results = {r["instrument_id"]: r for r in resp.json()}

        assert results[covered_id]["status"] == "ok"
        assert results[covered_id]["price"] == 200.0
        assert results[not_covered_id]["status"] == "missing"

        resp = client.get(f"/api/prices/{covered_id}")
        assert resp.json()["source"] == "yfinance"
    finally:
        app.dependency_overrides.clear()
