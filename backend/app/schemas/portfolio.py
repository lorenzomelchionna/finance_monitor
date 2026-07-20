from pydantic import BaseModel


class PositionOut(BaseModel):
    instrument_id: int
    instrument_name: str
    quantity: float
    price_currency: str
    price_status: str
    value_base: float | None
    cost_base: float | None
    pnl_base: float | None
    exclusion_reason: str | None


class PortfolioSummaryOut(BaseModel):
    base_currency: str
    positions: list[PositionOut]
    total_value_base: float
    total_cost_base: float
    total_pnl_base: float
    currency_exposure: dict[str, float]
