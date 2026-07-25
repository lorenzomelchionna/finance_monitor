"""Instrument management.

Instruments are created by the broker import, not by hand — positions
come from the transaction ledger (see positions_service). What remains
editable is the metadata the export can't provide: a display name, the
exchange-suffixed ticker yfinance needs, and whether the instrument
counts towards the portfolio.
"""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.instrument import Instrument
from app.schemas.instrument import InstrumentUpdate


def list_instruments(session: Session) -> list[Instrument]:
    return session.exec(select(Instrument).order_by(Instrument.name)).all()


def update_instrument(
    session: Session, instrument_id: int, payload: InstrumentUpdate
) -> Instrument | None:
    instrument = session.get(Instrument, instrument_id)
    if instrument is None:
        return None

    if payload.name is not None:
        instrument.name = payload.name
    if payload.ticker is not None:
        instrument.ticker = payload.ticker or None
        # A ticker is what makes automatic pricing possible; setting one
        # turns it on, clearing it turns it back off so refreshes don't
        # fail noisily on an unresolvable symbol.
        instrument.auto_price_enabled = bool(instrument.ticker)
    if payload.included is not None:
        instrument.included = payload.included

    instrument.updated_at = datetime.now(timezone.utc)
    session.add(instrument)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"Ticker '{payload.ticker}' is already used by another instrument") from exc
    session.refresh(instrument)
    return instrument
