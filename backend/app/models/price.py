"""PriceSnapshot: latest known price for an instrument.

Both automated (provider) and manual prices land in this same table,
distinguished by `source` — there is no separate "override" table. The
most recent row (by as_of) for an instrument wins. This keeps
pricing_service's "pick the freshest quote, degrade to manual" logic
simple: one table, one ORDER BY.
"""

import enum
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class PriceSource(str, enum.Enum):
    yfinance = "yfinance"
    manual = "manual"


class PriceSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)

    price: float
    currency: str
    source: PriceSource

    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
