from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionSign


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instrument_id: int
    isin: str
    name: str
    trade_date: date
    value_date: date | None
    sign: TransactionSign
    quantity: float
    currency: str
    price: float
    fx_rate: float
    gross_amount: float
    commissions: float


class SkippedInstrument(BaseModel):
    isin: str
    name: str


class ImportResultOut(BaseModel):
    imported: int
    duplicates: int
    skipped: list[SkippedInstrument]
