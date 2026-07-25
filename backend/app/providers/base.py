"""Provider abstraction: the seam between external market-data sources
(price/FX/composition) and the rest of the app.

Everything in this module is a plain dataclass/Protocol — no FastAPI, no
SQLModel — so a new source (a paid API, a CSV import, a different quote
vendor) can be added by writing one class here without touching
`domain/` or `api/`. `InstrumentRef` is the identity a provider needs;
it carries `id` (the DB primary key) alongside isin/ticker/currency so
that DB-backed providers (e.g. the manual fallback) and network-backed
providers (e.g. yfinance) can share the exact same Protocol shape.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


class Dimension(str, Enum):
    geography = "geography"
    sector = "sector"


@dataclass(frozen=True)
class InstrumentRef:
    id: int
    isin: str | None
    ticker: str | None
    currency: str


@dataclass(frozen=True)
class PriceQuote:
    price: float
    currency: str
    as_of: datetime


@dataclass(frozen=True)
class HistoryPoint:
    date: str  # ISO date (YYYY-MM-DD)
    close: float


@dataclass(frozen=True)
class FxRate:
    base: str
    quote: str
    rate: float
    as_of: datetime


@dataclass(frozen=True)
class BreakdownWeight:
    key: str
    weight: float


class PriceProvider(Protocol):
    def get_price(self, ref: InstrumentRef) -> PriceQuote | None: ...


class HistoryProvider(Protocol):
    """Full available daily close history for an instrument. Separate
    from PriceProvider so a source can offer spot quotes without history
    (or vice versa). Returns None on lookup failure, [] when the symbol
    resolved but has no data — callers distinguish 'couldn't fetch' from
    'genuinely empty'."""

    def get_history(self, ref: InstrumentRef) -> list[HistoryPoint] | None: ...


class FxProvider(Protocol):
    def get_rate(self, base: str, quote: str) -> FxRate | None: ...


class TickerProvider(Protocol):
    """Resolve an ISIN to an exchange-suffixed ticker usable for price
    lookups. Broker exports carry ISINs but rarely tickers, so without
    this every imported instrument would need one typed in by hand.
    Returns None when the symbol can't be resolved."""

    def resolve_ticker(self, isin: str) -> str | None: ...


class CompositionProvider(Protocol):
    """Look-through geo/sector weights for an instrument. Returns a map
    keyed by dimension ("geography" / "sector") — a single source page
    usually carries both, so one fetch yields both dimensions. Returns
    None on lookup failure; a dimension absent from the map means that
    source has no data for it (e.g. a bond ETF with no equity sectors)."""

    def get_breakdowns(self, ref: InstrumentRef) -> dict[str, list[BreakdownWeight]] | None: ...
