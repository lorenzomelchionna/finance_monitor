import itertools
from datetime import date

from app.models.transaction import Transaction, TransactionSign
from app.providers.base import InstrumentRef, PriceQuote


class FakeAutoProvider:
    """Stand-in for YFinanceProvider so tests never hit the network."""

    def __init__(self, quote: PriceQuote | None) -> None:
        self._quote = quote

    def get_price(self, ref: InstrumentRef) -> PriceQuote | None:
        return self._quote


_dedup_counter = itertools.count()


def buy(instrument, quantity: float, price: float, *, on: date | None = None, commissions: float = 0.0) -> Transaction:
    """Build a buy transaction — the only way a position exists now that
    holdings are derived from the ledger rather than entered by hand."""
    return Transaction(
        instrument_id=instrument.id,
        isin=instrument.isin or f"ISIN{instrument.id}",
        name=instrument.name,
        trade_date=on or date(2025, 1, 1),
        sign=TransactionSign.buy,
        quantity=quantity,
        currency=instrument.currency,
        price=price,
        gross_amount=quantity * price,
        commissions=commissions,
        dedup_key=f"test-{next(_dedup_counter)}",
    )
