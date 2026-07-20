from pydantic import BaseModel, Field, model_validator

from app.models.instrument import AssetClass
from app.schemas.instrument import InstrumentOut


class InstrumentInput(BaseModel):
    """Either point at an existing instrument by id, or describe a new
    one to create inline — matches the "crea Instrument inline se serve"
    requirement for holding creation. Matching for de-dup happens in
    holdings_service (by isin, then ticker) so re-adding the same
    instrument reuses the existing row instead of duplicating it."""

    instrument_id: int | None = None
    isin: str | None = None
    ticker: str | None = None
    name: str | None = None
    currency: str | None = None
    asset_class: AssetClass = AssetClass.etf
    auto_price_enabled: bool = True

    @model_validator(mode="after")
    def _check_shape(self) -> "InstrumentInput":
        if self.instrument_id is None:
            if not self.name or not self.currency or not (self.isin or self.ticker):
                raise ValueError(
                    "Provide instrument_id, or isin/ticker + name + currency to create a new instrument"
                )
        return self


class HoldingCreate(BaseModel):
    instrument: InstrumentInput
    quantity: float = Field(gt=0)
    avg_cost_price: float = Field(gt=0)
    cost_currency: str


class HoldingUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    avg_cost_price: float | None = Field(default=None, gt=0)
    cost_currency: str | None = None


class HoldingOut(BaseModel):
    id: int
    instrument: InstrumentOut
    quantity: float
    avg_cost_price: float
    cost_currency: str
