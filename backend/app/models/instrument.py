"""Instrument: the tradeable security itself (ETF, stock, bond, ...).

Decoupled from Holding so future features (multiple lots, price/composition
history) can attach to the instrument without duplicating identity data.
"""

import enum
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class AssetClass(str, enum.Enum):
    etf = "etf"
    stock = "stock"
    bond = "bond"
    cash = "cash"
    other = "other"


class Instrument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # At least one of isin/ticker should be set; both indexed for lookup.
    isin: str | None = Field(default=None, index=True, unique=True)
    ticker: str | None = Field(default=None, index=True, unique=True)
    name: str

    # ISO 4217 currency the instrument is quoted in (not necessarily the
    # currency of its underlying exposure — that's out of scope for v1).
    currency: str

    asset_class: AssetClass = Field(default=AssetClass.etf)

    # Per-instrument opt-out of automatic price fetching (e.g. instrument
    # not covered by the provider, or in liquidation) — forces manual pricing.
    auto_price_enabled: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
