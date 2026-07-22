from pydantic import BaseModel


class WeightSliceOut(BaseModel):
    key: str
    weight: float


class CompositionOut(BaseModel):
    # dimension ("geography" | "sector") -> slices sorted desc
    dimensions: dict[str, list[WeightSliceOut]]
    # dimension -> fraction of portfolio value covered by breakdown data
    coverage: dict[str, float]
    # dimension -> names of held instruments missing data for it
    missing: dict[str, list[str]]


class CompositionRefreshOut(BaseModel):
    updated: list[str]
    failed: list[str]
