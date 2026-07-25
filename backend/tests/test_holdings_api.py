"""Coverage of the instrument routes.

There is no create/delete: instruments come from the broker import and
positions are derived from the ledger. What these tests guard is the
metadata the export can't supply (name, ticker) and the include/exclude
toggle that decides what counts towards the portfolio.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.instrument import Instrument
from tests.helpers import buy


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app), engine


def _seed(engine, **kwargs) -> int:
    """Create one instrument with a buy, return its id."""
    defaults = dict(isin="IE00BK5BQT80", ticker="VWCE", name="Old Name", currency="EUR")
    defaults.update(kwargs)
    with Session(engine) as s:
        instrument = Instrument(**defaults)
        s.add(instrument)
        s.commit()
        s.refresh(instrument)
        s.add(buy(instrument, 10, 100.0))
        s.commit()
        return instrument.id


def test_positions_are_derived_from_the_ledger():
    client, engine = _client_with_fresh_db()
    try:
        _seed(engine)
        positions = client.get("/api/positions").json()
        assert len(positions) == 1
        assert positions[0]["quantity"] == 10
        assert positions[0]["avg_cost"] == 100.0
        assert positions[0]["transaction_count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_rename_instrument():
    client, engine = _client_with_fresh_db()
    try:
        instrument_id = _seed(engine)

        resp = client.put(f"/api/instruments/{instrument_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

        assert client.get("/api/positions").json()[0]["instrument"]["name"] == "New Name"

        assert client.put(f"/api/instruments/{instrument_id}", json={"name": ""}).status_code == 422
        assert client.put("/api/instruments/999999", json={"name": "Nope"}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_setting_a_ticker_enables_automatic_pricing():
    client, engine = _client_with_fresh_db()
    try:
        # Imported instruments start without a ticker, so auto-pricing is off.
        instrument_id = _seed(engine, ticker=None, auto_price_enabled=False)

        resp = client.put(f"/api/instruments/{instrument_id}", json={"ticker": "VWCE.MI"})
        assert resp.status_code == 200
        assert resp.json()["ticker"] == "VWCE.MI"
        assert resp.json()["auto_price_enabled"] is True

        # Clearing it turns pricing back off rather than failing on every refresh.
        resp = client.put(f"/api/instruments/{instrument_id}", json={"ticker": ""})
        assert resp.json()["ticker"] is None
        assert resp.json()["auto_price_enabled"] is False
    finally:
        app.dependency_overrides.clear()


def test_ticker_collision_is_rejected():
    client, engine = _client_with_fresh_db()
    try:
        first = _seed(engine, isin="AAA", ticker="MEUD", name="Amundi")
        _seed(engine, isin="BBB", ticker="EIMI", name="iShares")

        resp = client.put(f"/api/instruments/{first}", json={"ticker": "EIMI"})
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_excluding_an_instrument_drops_it_from_positions():
    client, engine = _client_with_fresh_db()
    try:
        instrument_id = _seed(engine)
        assert len(client.get("/api/positions").json()) == 1

        resp = client.put(f"/api/instruments/{instrument_id}", json={"included": False})
        assert resp.status_code == 200
        assert resp.json()["included"] is False

        # Excluded: gone from positions, but still listed and still owns
        # its transaction history.
        assert client.get("/api/positions").json() == []
        assert len(client.get("/api/instruments").json()) == 1
        assert len(client.get("/api/transactions").json()) == 1

        client.put(f"/api/instruments/{instrument_id}", json={"included": True})
        assert len(client.get("/api/positions").json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_excluded_instrument_leaves_the_portfolio_summary():
    client, engine = _client_with_fresh_db()
    try:
        instrument_id = _seed(engine)
        client.put(f"/api/instruments/{instrument_id}", json={"included": False})

        summary = client.get("/api/portfolio/summary").json()
        assert summary["positions"] == []
        assert summary["total_cost_base"] == 0.0
    finally:
        app.dependency_overrides.clear()


class FakeTickerProvider:
    def __init__(self, by_isin):
        self._by_isin = by_isin

    def resolve_ticker(self, isin: str):
        return self._by_isin.get(isin)


def test_resolve_tickers_fills_in_what_the_export_lacks(monkeypatch):
    """The broker export has no ticker, so imported instruments can't be
    priced until one is resolved."""
    from app.providers import registry

    client, engine = _client_with_fresh_db()
    try:
        known = _seed(engine, isin="IE00BK5BQT80", ticker=None, name="All World", auto_price_enabled=False)
        etc = _seed(engine, isin="IE00B8XB7377", ticker=None, name="Gold ETC", auto_price_enabled=False)

        monkeypatch.setitem(
            registry._TICKER_PROVIDERS,
            "justetf",
            FakeTickerProvider({"IE00BK5BQT80": "VWCE.MI"}),  # ETC unknown
        )

        body = client.post("/api/instruments/resolve-tickers").json()
        assert body["resolved"] == {"All World": "VWCE.MI"}
        assert body["unresolved"] == ["Gold ETC"]

        instruments = {i["id"]: i for i in client.get("/api/instruments").json()}
        # Resolved: ticker set and automatic pricing switched on.
        assert instruments[known]["ticker"] == "VWCE.MI"
        assert instruments[known]["auto_price_enabled"] is True
        # Unresolved: left for manual entry rather than guessed at.
        assert instruments[etc]["ticker"] is None
        assert instruments[etc]["auto_price_enabled"] is False
    finally:
        app.dependency_overrides.clear()
