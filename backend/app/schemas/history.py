from pydantic import BaseModel


class HistoryPointOut(BaseModel):
    date: str
    close: float
    invested: float | None = None  # cumulative invested for this instrument, None if no txns
    # Actual position value (held qty * close) — comparable to `invested`
    # for a gain/loss %, unlike `close` which is a per-unit price. None
    # before the first purchase or when there's no ledger for this
    # instrument.
    position_value: float | None = None


class InstrumentHistoryOut(BaseModel):
    instrument_id: int
    name: str
    ticker: str | None
    currency: str
    points: list[HistoryPointOut]


class PortfolioValuePointOut(BaseModel):
    date: str
    value: float
    invested: float  # cumulative capital invested as of this date


class PortfolioHistoryOut(BaseModel):
    base_currency: str
    series: list[InstrumentHistoryOut]
    portfolio: list[PortfolioValuePointOut]
    warnings: list[str]
