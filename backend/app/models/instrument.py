"""Instrument: the tradeable security itself (ETF, stock, bond, ...).

Instruments are created by the broker import — the Fineco movements
export is the source of truth for what was actually traded. Positions
(quantity, cost) are derived from the transaction ledger rather than
stored here; this row only carries identity, pricing hints, and whether
the user wants it counted towards the portfolio.
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

    # Whether this instrument counts towards the portfolio. The import
    # decides *what was traded*; this flag is the user's say over *what
    # to track* — excluding something without discarding its history.
    included: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
