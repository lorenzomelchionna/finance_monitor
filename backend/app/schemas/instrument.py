from pydantic import BaseModel, ConfigDict, Field

from app.models.instrument import AssetClass


class InstrumentUpdate(BaseModel):
    """Every field optional: the UI patches one thing at a time (rename,
    set a ticker, include/exclude)."""

    name: str | None = Field(default=None, min_length=1)
    ticker: str | None = None
    included: bool | None = None


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isin: str | None
    ticker: str | None
    name: str
    currency: str
    asset_class: AssetClass
    auto_price_enabled: bool
    included: bool


class InstrumentPositionOut(BaseModel):
    """An instrument plus the position derived from its transactions."""

    instrument: InstrumentOut
    quantity: float
    avg_cost: float
    invested: float
    commissions: float
    transaction_count: int
