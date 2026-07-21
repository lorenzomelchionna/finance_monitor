"""End-to-end coverage of GET /api/portfolio/history with a stubbed
history provider (no network)."""

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.holding import Holding
from app.models.instrument import Instrument
from app.providers import registry
from app.providers.base import HistoryPoint, InstrumentRef


class FakeHistoryProvider:
    def __init__(self, by_ticker: dict[str, list[HistoryPoint]]) -> None:
        self._by_ticker = by_ticker

    def get_history(self, ref: InstrumentRef) -> list[HistoryPoint] | None:
        return self._by_ticker.get(ref.ticker)


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app), engine


def test_portfolio_history_aggregates_and_reports_series(monkeypatch):
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            a = Instrument(ticker="AAA", name="Alpha", currency="EUR")
            b = Instrument(ticker="BBB", name="Beta", currency="EUR")
            s.add_all([a, b])
            s.commit()
            s.refresh(a)
            s.refresh(b)
            s.add_all([
                Holding(instrument_id=a.id, quantity=2, avg_cost_price=1, cost_currency="EUR"),
                Holding(instrument_id=b.id, quantity=1, avg_cost_price=1, cost_currency="EUR"),
            ])
            s.commit()

        fake = FakeHistoryProvider({
            "AAA": [HistoryPoint("2020-01-01", 100.0), HistoryPoint("2020-01-02", 110.0)],
            "BBB": [HistoryPoint("2020-01-01", 50.0), HistoryPoint("2020-01-02", 60.0)],
        })
        monkeypatch.setitem(registry._HISTORY_PROVIDERS, "yfinance", fake)

        resp = client.get("/api/portfolio/history")
        assert resp.status_code == 200
        body = resp.json()

        assert body["base_currency"] == "EUR"
        assert len(body["series"]) == 2
        assert body["warnings"] == []

        portfolio = body["portfolio"]
        assert portfolio[0]["value"] == 2 * 100 + 1 * 50  # 250
        assert portfolio[1]["value"] == 2 * 110 + 1 * 60  # 280
    finally:
        app.dependency_overrides.clear()


def test_portfolio_history_warns_on_unresolved_and_non_base_currency(monkeypatch):
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            eur = Instrument(ticker="EUR1", name="EurOk", currency="EUR")
            usd = Instrument(ticker="USD1", name="UsdAsset", currency="USD")
            broken = Instrument(ticker="NOPE", name="Unresolved", currency="EUR")
            s.add_all([eur, usd, broken])
            s.commit()
            for i in (eur, usd, broken):
                s.refresh(i)
            s.add_all([
                Holding(instrument_id=eur.id, quantity=1, avg_cost_price=1, cost_currency="EUR"),
                Holding(instrument_id=usd.id, quantity=1, avg_cost_price=1, cost_currency="USD"),
                Holding(instrument_id=broken.id, quantity=1, avg_cost_price=1, cost_currency="EUR"),
            ])
            s.commit()

        fake = FakeHistoryProvider({
            "EUR1": [HistoryPoint("2020-01-01", 10.0)],
            "USD1": [HistoryPoint("2020-01-01", 20.0)],
            # NOPE returns None (unresolved ticker)
        })
        monkeypatch.setitem(registry._HISTORY_PROVIDERS, "yfinance", fake)

        body = client.get("/api/portfolio/history").json()

        # USD charted individually but excluded from aggregate; only EUR1 in it.
        assert len(body["series"]) == 2  # EUR1 + USD1 (NOPE has no series)
        assert body["portfolio"][0]["value"] == 10.0
        assert any("USD" in w for w in body["warnings"])
        assert any("Unresolved" in w for w in body["warnings"])
    finally:
        app.dependency_overrides.clear()
