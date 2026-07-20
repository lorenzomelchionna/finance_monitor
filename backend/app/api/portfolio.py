from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.portfolio import PortfolioSummaryOut
from app.services.portfolio_service import get_portfolio_summary

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=PortfolioSummaryOut)
def portfolio_summary(session: Session = Depends(get_session)) -> PortfolioSummaryOut:
    summary = get_portfolio_summary(session)
    return PortfolioSummaryOut(
        base_currency=summary.base_currency,
        positions=[asdict(p) for p in summary.positions],
        total_value_base=summary.total_value_base,
        total_cost_base=summary.total_cost_base,
        total_pnl_base=summary.total_pnl_base,
        currency_exposure=summary.currency_exposure,
    )
