"""Chooses which price source to use for an instrument and degrades
gracefully: auto provider (if enabled) -> last manual entry -> missing.

This is the single seam the rest of the app depends on — swapping or
adding an auto provider means editing `_AUTO_PROVIDERS` here, nothing
else in domain/services/api changes.
"""

import enum

from sqlmodel import Session

from app.models.instrument import Instrument
from app.providers.base import InstrumentRef, PriceProvider, PriceQuote
from app.providers.manual_provider import ManualPriceProvider
from app.providers.yfinance_provider import YFinanceProvider


class PriceStatus(str, enum.Enum):
    ok = "ok"  # fresh quote from the auto provider
    manual = "manual"  # served from the last manually-entered price
    missing = "missing"  # no price available from any source


_AUTO_PROVIDERS: dict[str, PriceProvider] = {
    "yfinance": YFinanceProvider(),
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
