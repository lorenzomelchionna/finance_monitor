from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.db import get_session
from app.schemas.transaction import ImportResultOut, TransactionOut
from app.services import transactions_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_transactions(session: Session = Depends(get_session)) -> list:
    return transactions_service.list_transactions(session)


@router.post("/import", response_model=ImportResultOut)
async def import_transactions(
    file: UploadFile = File(...), session: Session = Depends(get_session)
) -> dict:
    """Import a Fineco 'Movimenti Dossier Titoli' xlsx. Only operations
    for instruments already in the portfolio are stored; re-importing an
    overlapping export is idempotent (dedup by natural key)."""
    data = await file.read()
    try:
        return transactions_service.import_fineco_xlsx(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
