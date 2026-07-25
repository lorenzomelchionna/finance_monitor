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

from app.config import get_settings
from app.models.instrument import Instrument
from app.providers.registry import resolve_ticker
from app.schemas.instrument import InstrumentUpdate


def list_instruments(session: Session) -> list[Instrument]:
    return session.exec(select(Instrument).order_by(Instrument.name)).all()


def resolve_missing_tickers(session: Session) -> dict:
    """Fill in tickers for instruments that don't have one, so imported
    positions can be priced automatically. Instruments the source can't
    resolve (ETCs, single stocks) are reported back for manual entry."""
    settings = get_settings()
    instruments = session.exec(select(Instrument)).all()
    used = {i.ticker for i in instruments if i.ticker}

    resolved: dict[str, str] = {}
    unresolved: list[str] = []

    for instrument in instruments:
        if instrument.ticker or not instrument.isin:
            continue
        ticker = resolve_ticker(instrument.isin, settings.default_composition_provider)
        if not ticker or ticker in used:
            unresolved.append(instrument.name)
            continue
        instrument.ticker = ticker
        instrument.auto_price_enabled = True
        instrument.updated_at = datetime.now(timezone.utc)
        session.add(instrument)
        used.add(ticker)
        resolved[instrument.name] = ticker

    session.commit()
    return {"resolved": resolved, "unresolved": unresolved}


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
