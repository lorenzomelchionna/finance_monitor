"""End-to-end coverage of /api/composition with a stubbed provider (no
network)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.holding import Holding
from app.models.instrument import Instrument
from app.models.price import PriceSnapshot, PriceSource
from app.providers import registry
from app.providers.base import BreakdownWeight, InstrumentRef


class FakeCompositionProvider:
    def __init__(self, by_isin):
        self._by_isin = by_isin

    def get_breakdowns(self, ref: InstrumentRef):
        return self._by_isin.get(ref.isin)


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app), engine


def test_refresh_then_aggregate(monkeypatch):
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            a = Instrument(isin="AAA", ticker="A.MI", name="Alpha", currency="EUR")
            b = Instrument(isin="BBB", ticker="B.MI", name="Beta", currency="EUR")
            s.add_all([a, b])
            s.commit()
            s.refresh(a)
            s.refresh(b)
            # Equal value: 10 units @ 100 each.
            s.add_all([
                Holding(instrument_id=a.id, quantity=10, avg_cost_price=100, cost_currency="EUR"),
                Holding(instrument_id=b.id, quantity=10, avg_cost_price=100, cost_currency="EUR"),
                PriceSnapshot(instrument_id=a.id, price=100, currency="EUR", source=PriceSource.manual, as_of=datetime.now(timezone.utc)),
                PriceSnapshot(instrument_id=b.id, price=100, currency="EUR", source=PriceSource.manual, as_of=datetime.now(timezone.utc)),
            ])
            s.commit()

        fake = FakeCompositionProvider({
            "AAA": {"geography": [BreakdownWeight("US", 1.0)], "sector": [BreakdownWeight("Tech", 1.0)]},
            "BBB": {"geography": [BreakdownWeight("Japan", 1.0)]},  # no sector
        })
        monkeypatch.setitem(registry._COMPOSITION_PROVIDERS, "justetf", fake)

        resp = client.post("/api/composition/refresh")
        assert resp.status_code == 200
        assert set(resp.json()["updated"]) == {"Alpha", "Beta"}

        agg = client.get("/api/composition").json()
        geo = {s["key"]: s["weight"] for s in agg["dimensions"]["geography"]}
        assert geo["US"] == 0.5 and geo["Japan"] == 0.5
        assert agg["coverage"]["geography"] == 1.0

        # Only Alpha has sector data -> Beta listed as missing, coverage 50%.
        assert agg["dimensions"]["sector"][0]["key"] == "Tech"
        assert agg["coverage"]["sector"] == 0.5
        assert agg["missing"]["sector"] == ["Beta"]
    finally:
        app.dependency_overrides.clear()


def test_refresh_reports_failures(monkeypatch):
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            a = Instrument(isin="AAA", ticker="A.MI", name="Alpha", currency="EUR")
            s.add(a)
            s.commit()
            s.refresh(a)
            s.add(Holding(instrument_id=a.id, quantity=1, avg_cost_price=100, cost_currency="EUR"))
            s.commit()

        # Provider returns None (fetch failed).
        monkeypatch.setitem(registry._COMPOSITION_PROVIDERS, "justetf", FakeCompositionProvider({}))
        resp = client.post("/api/composition/refresh")
        assert resp.json()["failed"] == ["Alpha"]
        assert resp.json()["updated"] == []
    finally:
        app.dependency_overrides.clear()
