"""Holding: a position held in the portfolio.

Modeled as one-to-many against Instrument (rather than a single row per
instrument) so multiple lots/purchases can be tracked later without a
schema change — today, in practice, it's one holding per instrument.

No purchase-time FX is stored: v1 currency-effect analysis is snapshot-only
(current value vs. current FX rate), not a historical return attribution.
See CLAUDE.md-adjacent plan doc for the rationale.
"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Holding(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)

    quantity: float
    avg_cost_price: float
    cost_currency: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
