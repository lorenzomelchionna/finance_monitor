"""Transaction: a single buy/sell operation imported from a broker
export (Fineco "Movimenti Dossier Titoli").

Distinct from Holding (the current net position) — this is the
immutable event log of what was actually traded, when, at what price.
It's the source of truth for real cost basis, money-weighted return
(XIRR) and the "when did I buy" markers on the history charts.

Linked to Instrument by FK; only operations whose ISIN matches an
instrument already in the portfolio are imported (per the user's "solo
per quelli presenti in portafoglio"). `dedup_key` is a stable signature
so re-importing an overlapping export doesn't duplicate rows.
"""

import enum
from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class TransactionSign(str, enum.Enum):
    buy = "A"  # Acquisto
    sell = "V"  # Vendita


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)

    isin: str = Field(index=True)
    name: str  # raw security name from the broker export
    trade_date: date = Field(index=True)  # "Operazione"
    value_date: date | None = None  # "Data valuta"
    sign: TransactionSign
    quantity: float
    currency: str
    price: float
    fx_rate: float = 1.0  # "Cambio" (broker's FX at trade time; 1 for EUR)
    gross_amount: float  # "Controvalore" (qty * price, broker-reported)
    commissions: float = 0.0  # summed commission columns

    # Stable natural key to make re-import idempotent.
    dedup_key: str = Field(index=True, unique=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
