"""End-to-end coverage of GET /api/portfolio/summary: two positions (one
EUR, one USD-with-manual-price) valued together. Positions come from the
transaction ledger; the FX provider is mocked so the test never touches
the network."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.instrument import Instrument
from app.providers import registry
from app.providers.base import FxRate
from app.services import pricing_service
from tests.helpers import buy


class FakeFxProvider:
    def __init__(self, rate: float) -> None:
        self._rate = rate

    def get_rate(self, base: str, quote: str):
        return FxRate(base=base, quote=quote, rate=self._rate, as_of=datetime.now(timezone.utc))


def test_portfolio_summary_mixed_currencies(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    monkeypatch.setitem(registry._FX_PROVIDERS, "yfinance", FakeFxProvider(0.9))

    try:
        with Session(engine) as s:
            eur_instrument = Instrument(ticker="VWCE.DE", name="Vanguard All-World", currency="EUR")
            usd_instrument = Instrument(
                ticker="ILLIQUID", name="Illiquid fund", currency="USD", auto_price_enabled=False
            )
            s.add_all([eur_instrument, usd_instrument])
            s.commit()
            s.refresh(eur_instrument)
            s.refresh(usd_instrument)

            s.add_all([buy(eur_instrument, 10, 90.0), buy(usd_instrument, 2, 100.0)])
            s.commit()

            pricing_service.set_manual_price(s, eur_instrument.id, 100.0, "EUR")
            pricing_service.set_manual_price(s, usd_instrument.id, 150.0, "USD")

        client = TestClient(app)
        resp = client.get("/api/portfolio/summary")
        assert resp.status_code == 200
        body = resp.json()

        assert body["base_currency"] == "EUR"
        assert len(body["positions"]) == 2
        assert body["total_value_base"] == 10 * 100.0 + 2 * 150.0 * 0.9
        # Ledger amounts are already in the base currency (no FX applied to cost).
        assert body["total_cost_base"] == 10 * 90.0 + 2 * 100.0
        assert set(body["currency_exposure"].keys()) == {"EUR", "USD"}
        assert all(p["exclusion_reason"] is None for p in body["positions"])
    finally:
        app.dependency_overrides.clear()


def test_portfolio_summary_reports_missing_price():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    try:
        with Session(engine) as s:
            instrument = Instrument(ticker="NEW", name="Brand new", currency="EUR")
            s.add(instrument)
            s.commit()
            s.refresh(instrument)
            s.add(buy(instrument, 1, 10.0))
            s.commit()

        client = TestClient(app)
        resp = client.get("/api/portfolio/summary")
        body = resp.json()

        assert body["positions"][0]["exclusion_reason"] == "missing_price"
        assert body["total_value_base"] == 0.0
    finally:
        app.dependency_overrides.clear()
