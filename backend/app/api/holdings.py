"""Instrument routes.

There is no create/delete here by design: the broker import is the
source of truth for what exists and what is held. The only writes are
metadata edits — name, ticker, and the include/exclude toggle.
"""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.instrument import Instrument
from app.models.transaction import Transaction
from app.schemas.instrument import (
    InstrumentOut,
    InstrumentPositionOut,
    InstrumentUpdate,
    TickerResolveOut,
)
from app.services import holdings_service
from app.services.positions_service import get_positions

router = APIRouter(prefix="/api", tags=["instruments"])


@router.get("/instruments", response_model=list[InstrumentOut])
def list_instruments(session: Session = Depends(get_session)) -> list[Instrument]:
    """Every instrument the import has ever seen, included or not."""
    return holdings_service.list_instruments(session)


@router.put("/instruments/{instrument_id}", response_model=InstrumentOut)
def update_instrument(
    instrument_id: int, payload: InstrumentUpdate, session: Session = Depends(get_session)
) -> Instrument:
    try:
        instrument = holdings_service.update_instrument(session, instrument_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument


@router.post("/instruments/resolve-tickers", response_model=TickerResolveOut)
def resolve_tickers(session: Session = Depends(get_session)) -> TickerResolveOut:
    """Look up the exchange ticker for instruments that lack one, so
    imported positions can be priced without typing anything."""
    return TickerResolveOut.model_validate(holdings_service.resolve_missing_tickers(session))


@router.get("/positions", response_model=list[InstrumentPositionOut])
def list_positions(session: Session = Depends(get_session)) -> list[InstrumentPositionOut]:
    """Positions derived from the transaction ledger, for the instruments
    the user has included."""
    counts = Counter(t.instrument_id for t in session.exec(select(Transaction)).all())
    return [
        InstrumentPositionOut(
            instrument=InstrumentOut.model_validate(p.instrument),
            quantity=p.quantity,
            avg_cost=p.avg_cost,
            invested=p.invested,
            commissions=p.commissions,
            transaction_count=counts.get(p.instrument.id, 0),
        )
        for p in get_positions(session)
    ]
