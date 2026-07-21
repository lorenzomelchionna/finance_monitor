from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.history import PortfolioHistoryOut
from app.schemas.portfolio import PortfolioSummaryOut
from app.services.history_service import get_portfolio_history
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
        xirr=summary.xirr,
    )


@router.get("/history", response_model=PortfolioHistoryOut)
def portfolio_history(session: Session = Depends(get_session)) -> PortfolioHistoryOut:
    """Full available daily history per held instrument + the aggregate
    portfolio value series. Fetched from the price provider on each call
    (yfinance period=max); the frontend caches it and does horizon
    slicing / smoothing client-side, so switching views hits no network."""
    return PortfolioHistoryOut.model_validate(get_portfolio_history(session))
