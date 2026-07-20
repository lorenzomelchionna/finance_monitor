"""Chooses which price source to use for an instrument and degrades
gracefully: auto provider (if enabled) -> last manual entry -> missing.

This is the single seam the rest of the app depends on — swapping or
adding an auto provider means editing `_AUTO_PROVIDERS` here, nothing
else in domain/services/api changes.
"""

import enum

from sqlmodel import Session

from app.models.instrument import Instrument
from app.providers.base import FxProvider, InstrumentRef, PriceProvider, PriceQuote
from app.providers.manual_provider import ManualPriceProvider
from app.providers.yfinance_provider import YFinanceProvider


class PriceStatus(str, enum.Enum):
    ok = "ok"  # fresh quote from the auto provider
    manual = "manual"  # served from the last manually-entered price
    missing = "missing"  # no price available from any source


_yfinance = YFinanceProvider()

_AUTO_PROVIDERS: dict[str, PriceProvider] = {
    "yfinance": _yfinance,
}

# Same instance as _AUTO_PROVIDERS: YFinanceProvider implements both
# Price and Fx. No manual FX fallback exists in v1 (no data model for
# it) — an unavailable rate just means the position is excluded from
# EUR totals (see domain/portfolio.py's "missing_fx" status).
_FX_PROVIDERS: dict[str, FxProvider] = {
    "yfinance": _yfinance,
}


def to_instrument_ref(instrument: Instrument) -> InstrumentRef:
    return InstrumentRef(
        id=instrument.id,
        isin=instrument.isin,
        ticker=instrument.ticker,
        currency=instrument.currency,
    )


def resolve_price(
    instrument: Instrument, session: Session, auto_provider_name: str
) -> tuple[PriceQuote | None, PriceStatus]:
    ref = to_instrument_ref(instrument)

    if instrument.auto_price_enabled:
        provider = _AUTO_PROVIDERS.get(auto_provider_name)
        if provider is not None:
            quote = provider.get_price(ref)
            if quote is not None:
                return quote, PriceStatus.ok

    manual_quote = ManualPriceProvider(session).get_price(ref)
    if manual_quote is not None:
        return manual_quote, PriceStatus.manual

    return None, PriceStatus.missing


def resolve_fx_rate(source_currency: str, target_currency: str, provider_name: str) -> float | None:
    """Units of `target_currency` per 1 unit of `source_currency`, i.e.
    multiply an amount in `source_currency` by this to get `target_currency`."""
    if source_currency == target_currency:
        return 1.0

    provider = _FX_PROVIDERS.get(provider_name)
    if provider is None:
        return None

    rate = provider.get_rate(source_currency, target_currency)
    return rate.rate if rate is not None else None
