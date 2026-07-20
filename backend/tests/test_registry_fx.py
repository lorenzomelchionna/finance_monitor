from datetime import datetime, timezone

from app.providers import registry
from app.providers.base import FxRate
from app.providers.registry import resolve_fx_rate


class FakeFxProvider:
    def __init__(self, rate: FxRate | None) -> None:
        self._rate = rate

    def get_rate(self, base: str, quote: str):
        return self._rate


def test_resolve_fx_rate_same_currency_shortcut():
    assert resolve_fx_rate("EUR", "EUR", "yfinance") == 1.0


def test_resolve_fx_rate_delegates_to_provider(monkeypatch):
    fake_rate = FxRate(base="USD", quote="EUR", rate=0.9, as_of=datetime.now(timezone.utc))
    monkeypatch.setitem(registry._FX_PROVIDERS, "yfinance", FakeFxProvider(fake_rate))

    assert resolve_fx_rate("USD", "EUR", "yfinance") == 0.9


def test_resolve_fx_rate_returns_none_when_provider_has_no_rate(monkeypatch):
    monkeypatch.setitem(registry._FX_PROVIDERS, "yfinance", FakeFxProvider(None))

    assert resolve_fx_rate("JPY", "EUR", "yfinance") is None


def test_resolve_fx_rate_returns_none_for_unknown_provider():
    assert resolve_fx_rate("USD", "EUR", "not-a-real-provider") is None
