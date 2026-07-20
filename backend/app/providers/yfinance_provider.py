"""yfinance-backed PriceProvider + FxProvider.

yfinance is an unofficial, unauthenticated API: it's rate-limited and
frequently lacks coverage for European UCITS ETFs (ISIN-only lookups,
exchange-suffixed tickers like .MI/.DE, funds in liquidation). Any
lookup failure or missing field returns None rather than raising, so
the registry can degrade to the manual provider without a crash.
"""

import logging
from datetime import datetime, timezone

import yfinance as yf

from app.providers.base import FxRate, InstrumentRef, PriceQuote

logger = logging.getLogger(__name__)


class YFinanceProvider:
    def get_price(self, ref: InstrumentRef) -> PriceQuote | None:
        if not ref.ticker:
            return None
        try:
            fast_info = yf.Ticker(ref.ticker).fast_info
            price = fast_info.get("lastPrice")
            currency = fast_info.get("currency") or ref.currency
        except Exception:
            logger.warning("yfinance price lookup failed for %s", ref.ticker, exc_info=True)
            return None

        if price is None:
            return None
        return PriceQuote(price=float(price), currency=currency, as_of=datetime.now(timezone.utc))

    def get_rate(self, base: str, quote: str) -> FxRate | None:
        if base == quote:
            return FxRate(base=base, quote=quote, rate=1.0, as_of=datetime.now(timezone.utc))

        symbol = f"{base}{quote}=X"
        try:
            fast_info = yf.Ticker(symbol).fast_info
            rate = fast_info.get("lastPrice")
        except Exception:
            logger.warning("yfinance FX lookup failed for %s", symbol, exc_info=True)
            return None

        if rate is None:
            return None
        return FxRate(base=base, quote=quote, rate=float(rate), as_of=datetime.now(timezone.utc))
