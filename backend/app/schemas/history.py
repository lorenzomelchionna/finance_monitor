from pydantic import BaseModel


class HistoryPointOut(BaseModel):
    date: str
    close: float


class InstrumentHistoryOut(BaseModel):
    instrument_id: int
    name: str
    ticker: str | None
    currency: str
    points: list[HistoryPointOut]


class PortfolioValuePointOut(BaseModel):
    date: str
    value: float


class PortfolioHistoryOut(BaseModel):
    base_currency: str
    series: list[InstrumentHistoryOut]
    portfolio: list[PortfolioValuePointOut]
    warnings: list[str]
