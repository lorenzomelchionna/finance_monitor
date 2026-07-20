"""CompositionBreakdown: geographic/sector look-through weights for an
instrument (e.g. what VWCE is actually made of).

v1 status: SCHEMA ONLY. No UI, no aggregation endpoint, no population
logic yet — see plan's "Roadmap / Future steps". The table exists now so
that whichever population strategy Lorenzo picks later (manual entry, CSV
import from provider fund pages, paid API) plugs into the same shape
without a migration. `source` is what makes it pluggable: aggregation
logic (future) can prefer/mix rows by source without caring how they
got there.
"""

import enum

from sqlmodel import Field, SQLModel


class BreakdownDimension(str, enum.Enum):
    geography = "geography"
    sector = "sector"


class BreakdownSource(str, enum.Enum):
    manual = "manual"
    csv = "csv"
    api = "api"


class CompositionBreakdown(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)

    dimension: BreakdownDimension
    key: str  # e.g. "US", "Technology"
    weight: float  # 0..1, expected to sum to ~1 per (instrument, dimension)
    source: BreakdownSource = Field(default=BreakdownSource.manual)
