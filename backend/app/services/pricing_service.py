"""Orchestrates provider lookups + persistence for prices.

This is the seam between `providers/` (external data, no DB access) and
`api/` (thin routes): it decides what gets written to PriceSnapshot and
in what shape results are reported back.
"""

from sqlmodel import Session, select

from app.config import get_settings
from app.models.instrument import Instrument
from app.models.price import PriceSnapshot, PriceSource
from app.providers.registry import PriceStatus, resolve_price


def refresh_all_prices(session: Session) -> list[dict]:
    """Resolve a price for every instrument and persist a new snapshot
    only when the auto provider actually returned a fresh quote — a
    `manual` result means an existing manual row already covers it, and
    `missing` has nothing to persist."""
    settings = get_settings()
    instruments = session.exec(select(Instrument)).all()

    results = []
    for instrument in instruments:
        quote, status = resolve_price(instrument, session, settings.default_price_provider)

        if status == PriceStatus.ok and quote is not None:
            session.add(
                PriceSnapshot(
                    instrument_id=instrument.id,
                    price=quote.price,
                    currency=quote.currency,
                    source=PriceSource.yfinance,
                    as_of=quote.as_of,
                )
            )

        results.append(
            {
                "instrument_id": instrument.id,
                "status": status,
                "price": quote.price if quote else None,
                "currency": quote.currency if quote else None,
            }
        )

    session.commit()
    return results


def set_manual_price(session: Session, instrument_id: int, price: float, currency: str) -> PriceSnapshot | None:
    instrument = session.get(Instrument, instrument_id)
    if instrument is None:
        return None

    snapshot = PriceSnapshot(
        instrument_id=instrument_id,
        price=price,
        currency=currency,
        source=PriceSource.manual,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def get_latest_price(session: Session, instrument_id: int) -> PriceSnapshot | None:
    statement = (
        select(PriceSnapshot)
        .where(PriceSnapshot.instrument_id == instrument_id)
        .order_by(PriceSnapshot.as_of.desc())
    )
    return session.exec(statement).first()
