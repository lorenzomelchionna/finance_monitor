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


class FxProvider(Protocol):
    def get_rate(self, base: str, quote: str) -> FxRate | None: ...


class CompositionProvider(Protocol):
    """v1: interface only. No implementation is wired up yet — see the
    plan's Roadmap for the CSV-import / paid-API options under
    consideration."""

    def get_breakdown(self, ref: InstrumentRef, dimension: Dimension) -> list[BreakdownWeight] | None: ...
