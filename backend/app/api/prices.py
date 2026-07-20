from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas.price import ManualPriceIn, PriceOut, PriceStatusOut
from app.services import pricing_service

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.post("/refresh", response_model=list[PriceStatusOut])
def refresh_prices(session: Session = Depends(get_session)) -> list[dict]:
    return pricing_service.refresh_all_prices(session)


@router.put("/{instrument_id}", response_model=PriceOut)
def set_manual_price(
    instrument_id: int, payload: ManualPriceIn, session: Session = Depends(get_session)
) -> PriceOut:
    snapshot = pricing_service.set_manual_price(session, instrument_id, payload.price, payload.currency)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return PriceOut(
        instrument_id=instrument_id,
        price=snapshot.price,
        currency=snapshot.currency,
        source=snapshot.source,
        as_of=snapshot.as_of,
    )


@router.get("/{instrument_id}", response_model=PriceOut)
def get_price(instrument_id: int, session: Session = Depends(get_session)) -> PriceOut:
    snapshot = pricing_service.get_latest_price(session, instrument_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No price available for this instrument")
    return PriceOut(
        instrument_id=instrument_id,
        price=snapshot.price,
        currency=snapshot.currency,
        source=snapshot.source,
        as_of=snapshot.as_of,
    )
