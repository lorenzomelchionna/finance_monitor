from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.composition import CompositionOut, CompositionRefreshOut
from app.services import composition_service

router = APIRouter(prefix="/api/composition", tags=["composition"])


@router.get("", response_model=CompositionOut)
def get_composition(session: Session = Depends(get_session)) -> CompositionOut:
    """Value-weighted geographic + sector exposure of the portfolio, from
    stored look-through breakdowns."""
    return CompositionOut.model_validate(composition_service.get_composition(session))


@router.post("/refresh", response_model=CompositionRefreshOut)
def refresh_composition(session: Session = Depends(get_session)) -> CompositionRefreshOut:
    """Fetch geo/sector breakdowns for every held instrument from the
    composition provider (JustETF) and store them."""
    return CompositionRefreshOut.model_validate(composition_service.refresh_composition(session))
