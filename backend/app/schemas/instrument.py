from pydantic import BaseModel, ConfigDict, Field

from app.models.instrument import AssetClass


class InstrumentUpdate(BaseModel):
    name: str = Field(min_length=1)


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isin: str | None
    ticker: str | None
    name: str
    currency: str
    asset_class: AssetClass
    auto_price_enabled: bool
