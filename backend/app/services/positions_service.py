"""Derives current positions from the transaction ledger.

The broker export is the source of truth: quantity and cost basis come
from the imported buys and sells, never from hand-entered figures. This
replaces the old manually-maintained Holding table — one place that
answers "what do I hold, and what did it cost", so the portfolio,
history and composition services can't drift apart.

Only instruments the user has marked `included` and that still have a
positive net quantity count as positions.
"""

from dataclasses import dataclass

from sqlmodel import Session, select

from app.domain.performance import TxnLike, cost_basis_by_instrument
from app.models.instrument import Instrument
from app.models.transaction import Transaction


@dataclass(frozen=True)
class DerivedPosition:
    instrument: Instrument
    quantity: float
    avg_cost: float  # per unit, commissions included
    invested: float  # total cash in, commissions included
    commissions: float


def load_txn_likes(session: Session) -> list[TxnLike]:
    """Ledger rows in the shape the pure performance math expects."""
    return [
        TxnLike(
            instrument_id=t.instrument_id,
            trade_date=t.trade_date,
            sign=t.sign.value,
            quantity=t.quantity,
            price=t.price,
            gross_amount=t.gross_amount,
            commissions=t.commissions,
        )
        for t in session.exec(select(Transaction)).all()
    ]


def get_positions(session: Session) -> list[DerivedPosition]:
    basis = cost_basis_by_instrument(load_txn_likes(session))
    instruments = {i.id: i for i in session.exec(select(Instrument)).all()}

    positions: list[DerivedPosition] = []
    for instrument_id, cb in basis.items():
        instrument = instruments.get(instrument_id)
        if instrument is None or not instrument.included:
            continue
        if cb.quantity <= 0:  # fully sold out
            continue
        positions.append(
            DerivedPosition(
                instrument=instrument,
                quantity=cb.quantity,
                avg_cost=cb.avg_cost,
                invested=cb.invested,
                commissions=cb.commissions,
            )
        )
    positions.sort(key=lambda p: p.instrument.name)
    return positions


def get_quantities(session: Session) -> dict[int, float]:
    """instrument_id -> held quantity, for the included instruments."""
    return {p.instrument.id: p.quantity for p in get_positions(session)}
