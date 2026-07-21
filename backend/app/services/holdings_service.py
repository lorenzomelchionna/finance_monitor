"""Holdings CRUD orchestration.

Resolves/creates the Instrument a holding points to — matching on isin
then ticker so re-adding the same instrument reuses the existing row
instead of duplicating it — then manages the Holding row itself.
"""

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.holding import Holding
from app.models.instrument import Instrument
from app.schemas.holding import HoldingCreate, HoldingUpdate, InstrumentInput
from app.schemas.instrument import InstrumentUpdate


def _resolve_instrument(session: Session, spec: InstrumentInput) -> Instrument:
    if spec.instrument_id is not None:
        instrument = session.get(Instrument, spec.instrument_id)
        if instrument is None:
            raise ValueError(f"Instrument {spec.instrument_id} not found")
        return instrument

    existing = None
    if spec.isin:
        existing = session.exec(select(Instrument).where(Instrument.isin == spec.isin)).first()
    if existing is None and spec.ticker:
        existing = session.exec(select(Instrument).where(Instrument.ticker == spec.ticker)).first()
    if existing is not None:
        return existing

    instrument = Instrument(
        isin=spec.isin,
        ticker=spec.ticker,
        name=spec.name,
        currency=spec.currency,
        asset_class=spec.asset_class,
        auto_price_enabled=spec.auto_price_enabled,
    )
    session.add(instrument)
    session.commit()
    session.refresh(instrument)
    return instrument


def list_instruments(session: Session) -> list[Instrument]:
    return session.exec(select(Instrument)).all()


def list_holdings(session: Session) -> list[Holding]:
    return session.exec(select(Holding)).all()


def update_instrument(
    session: Session, instrument_id: int, payload: InstrumentUpdate
) -> Instrument | None:
    instrument = session.get(Instrument, instrument_id)
    if instrument is None:
        return None
    instrument.name = payload.name
    instrument.updated_at = datetime.now(timezone.utc)
    session.add(instrument)
    session.commit()
    session.refresh(instrument)
    return instrument


def create_holding(session: Session, payload: HoldingCreate) -> Holding:
    instrument = _resolve_instrument(session, payload.instrument)
    holding = Holding(
        instrument_id=instrument.id,
        quantity=payload.quantity,
        avg_cost_price=payload.avg_cost_price,
        cost_currency=payload.cost_currency,
    )
    session.add(holding)
    session.commit()
    session.refresh(holding)
    return holding


def update_holding(session: Session, holding_id: int, payload: HoldingUpdate) -> Holding | None:
    holding = session.get(Holding, holding_id)
    if holding is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(holding, key, value)
    holding.updated_at = datetime.now(timezone.utc)
    session.add(holding)
    session.commit()
    session.refresh(holding)
    return holding


def delete_holding(session: Session, holding_id: int) -> bool:
    holding = session.get(Holding, holding_id)
    if holding is None:
        return False
    session.delete(holding)
    session.commit()
    return True
