from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from app.db import get_session
from app.models.instrument import Instrument
from app.schemas.holding import HoldingCreate, HoldingOut, HoldingUpdate
from app.schemas.instrument import InstrumentOut, InstrumentUpdate
from app.services import holdings_service

router = APIRouter(prefix="/api", tags=["holdings"])


def _to_holding_out(session: Session, holding) -> HoldingOut:
    instrument = session.get(Instrument, holding.instrument_id)
    return HoldingOut(
        id=holding.id,
        instrument=InstrumentOut.model_validate(instrument),
        quantity=holding.quantity,
        avg_cost_price=holding.avg_cost_price,
        cost_currency=holding.cost_currency,
    )


@router.get("/instruments", response_model=list[InstrumentOut])
def list_instruments(session: Session = Depends(get_session)) -> list[Instrument]:
    return holdings_service.list_instruments(session)


@router.put("/instruments/{instrument_id}", response_model=InstrumentOut)
def update_instrument(
    instrument_id: int, payload: InstrumentUpdate, session: Session = Depends(get_session)
) -> Instrument:
    instrument = holdings_service.update_instrument(session, instrument_id, payload)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument


@router.get("/holdings", response_model=list[HoldingOut])
def list_holdings(session: Session = Depends(get_session)) -> list[HoldingOut]:
    return [_to_holding_out(session, h) for h in holdings_service.list_holdings(session)]


@router.post("/holdings", response_model=HoldingOut, status_code=201)
def create_holding(payload: HoldingCreate, session: Session = Depends(get_session)) -> HoldingOut:
    try:
        holding = holdings_service.create_holding(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_holding_out(session, holding)


@router.put("/holdings/{holding_id}", response_model=HoldingOut)
def update_holding(
    holding_id: int, payload: HoldingUpdate, session: Session = Depends(get_session)
) -> HoldingOut:
    holding = holdings_service.update_holding(session, holding_id, payload)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return _to_holding_out(session, holding)


@router.delete("/holdings/{holding_id}", status_code=204)
def delete_holding(holding_id: int, session: Session = Depends(get_session)) -> Response:
    deleted = holdings_service.delete_holding(session, holding_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Holding not found")
    return Response(status_code=204)
