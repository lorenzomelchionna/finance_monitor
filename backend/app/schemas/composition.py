from pydantic import BaseModel


class WeightSliceOut(BaseModel):
    key: str
    weight: float


class InstrumentCompositionOut(BaseModel):
    instrument_id: int
    name: str
    ticker: str | None
    # dimension -> slices sorted desc
    dimensions: dict[str, list[WeightSliceOut]]


class CompositionOut(BaseModel):
    # dimension ("geography" | "sector") -> slices sorted desc
    dimensions: dict[str, list[WeightSliceOut]]
    # dimension -> fraction of portfolio value covered by breakdown data
    coverage: dict[str, float]
    # dimension -> names of held instruments missing data for it
    missing: dict[str, list[str]]
    # per-instrument breakdowns, ordered by market value desc
    instruments: list[InstrumentCompositionOut]


class CompositionRefreshOut(BaseModel):
    updated: list[str]
    failed: list[str]
