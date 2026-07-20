"""Registry/fallback behavior: auto -> manual -> missing degradation,
and the auto_price_enabled per-instrument opt-out. The real YFinanceProvider
is never exercised here (network) — it's swapped for a fake via
monkeypatching the registry's provider map."""

from datetime import datetime, timezone

from app.models.instrument import Instrument
from app.providers import registry
from app.providers.base import PriceQuote
from app.providers.registry import PriceStatus, resolve_price
from app.services import pricing_service
from tests.helpers import FakeAutoProvider


def _make_instrument(session, **kwargs) -> Instrument:
    instrument = Instrument(ticker=kwargs.pop("ticker", "TICK"), name="Test", currency="EUR", **kwargs)
    session.add(instrument)
    session.commit()
    session.refresh(instrument)
    return instrument


def test_resolve_price_uses_auto_provider_when_available(session, monkeypatch):
    instrument = _make_instrument(session)
    quote = PriceQuote(price=110.0, currency="EUR", as_of=datetime.now(timezone.utc))
    monkeypatch.setitem(registry._AUTO_PROVIDERS, "yfinance", FakeAutoProvider(quote))

    result_quote, status = resolve_price(instrument, session, "yfinance")

    assert status == PriceStatus.ok
    assert result_quote.price == 110.0


def test_resolve_price_falls_back_to_manual_when_auto_has_no_coverage(session, monkeypatch):
    instrument = _make_instrument(session)
    monkeypatch.setitem(registry._AUTO_PROVIDERS, "yfinance", FakeAutoProvider(None))
    pricing_service.set_manual_price(session, instrument.id, 42.0, "EUR")

    quote, status = resolve_price(instrument, session, "yfinance")

    assert status == PriceStatus.manual
    assert quote.price == 42.0


def test_resolve_price_missing_when_no_source_available(session, monkeypatch):
    instrument = _make_instrument(session)
    monkeypatch.setitem(registry._AUTO_PROVIDERS, "yfinance", FakeAutoProvider(None))

    quote, status = resolve_price(instrument, session, "yfinance")

    assert status == PriceStatus.missing
    assert quote is None


def test_resolve_price_respects_auto_price_disabled(session, monkeypatch):
    instrument = _make_instrument(session, auto_price_enabled=False)
    auto_quote = PriceQuote(price=999.0, currency="EUR", as_of=datetime.now(timezone.utc))
    monkeypatch.setitem(registry._AUTO_PROVIDERS, "yfinance", FakeAutoProvider(auto_quote))

    # Auto is disabled for this instrument, so even though the provider
    # *would* return data, it must not be used — falls through to manual
    # (none set yet) -> missing.
    quote, status = resolve_price(instrument, session, "yfinance")

    assert status == PriceStatus.missing
    assert quote is None
