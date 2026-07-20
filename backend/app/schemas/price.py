from datetime import datetime

from pydantic import BaseModel, Field

from app.models.price import PriceSource
from app.providers.registry import PriceStatus


class PriceStatusOut(BaseModel):
    instrument_id: int
    status: PriceStatus
    price: float | None = None
    currency: str | None = None


class ManualPriceIn(BaseModel):
    price: float = Field(gt=0)
    currency: str


class PriceOut(BaseModel):
    instrument_id: int
    price: float
    currency: str
    source: PriceSource
    as_of: datetime
