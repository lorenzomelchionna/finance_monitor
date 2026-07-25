from typing import Literal

from pydantic import BaseModel, Field


class MonteCarloRequest(BaseModel):
    seed_capital: float = Field(ge=0)
    monthly_contribution: float = Field(ge=0)
    years: int = Field(gt=0, le=60)
    expected_annual_return: float
    annual_volatility: float = Field(ge=0)
    n_paths: int = Field(default=10_000, ge=100, le=50_000)
    random_seed: int | None = None
    # "student_t" is the default: Gaussian shocks make a -30% month
    # effectively impossible, which flatters the downside.
    distribution: Literal["normal", "student_t"] = "student_t"
    degrees_of_freedom: float = Field(default=5.0, gt=2, le=50)


class MonteCarloResponse(BaseModel):
    months: list[int]
    p5: list[float]
    p25: list[float]
    p50: list[float]
    p75: list[float]
    p95: list[float]
    final_mean: float
    final_median: float
    final_p5: float
    final_p95: float
    prob_below_contributed: float
    total_contributed: float
    median_max_drawdown: float
    worst_max_drawdown: float
