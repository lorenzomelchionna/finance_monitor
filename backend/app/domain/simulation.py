"""Monte Carlo simulation of a PAC (piano di accumulo): monthly
contributions into a lump-sum seed capital, compounded via monthly
geometric Brownian motion steps.

Pure numpy — no FastAPI/SQLModel/provider imports — so this is
independently unit-testable and fast enough to run thousands of paths
interactively from an API call.

Modeling convention: each month, the existing balance grows by a random
lognormal factor first, then that month's contribution is added at the
end of the month (so a newly-added contribution starts compounding the
following month, not the same one).

v1 scope: a single GBM regime (constant mu/sigma) for the whole
horizon — no fat tails, no regime shifts. Historical stress-test
scenarios (2008/2020/2022) are tracked in the plan's Roadmap as a
separate, complementary analysis.
"""

from dataclasses import dataclass

import numpy as np

PERCENTILES = (5, 25, 50, 75, 95)


@dataclass(frozen=True)
class SimulationParams:
    seed_capital: float
    monthly_contribution: float
    years: int
    expected_annual_return: float  # e.g. 0.07 for 7%
    annual_volatility: float  # e.g. 0.15 for 15%
    n_paths: int = 10_000
    random_seed: int | None = None


@dataclass(frozen=True)
class SimulationResult:
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


def run_montecarlo(params: SimulationParams) -> SimulationResult:
    n_months = params.years * 12
    monthly_return = (1 + params.expected_annual_return) ** (1 / 12) - 1
    monthly_vol = params.annual_volatility / (12**0.5)

    rng = np.random.default_rng(params.random_seed)

    paths = np.empty((params.n_paths, n_months + 1))
    paths[:, 0] = params.seed_capital

    # Lognormal shocks: mu adjusted by -0.5*sigma^2 so E[exp(shock)]
    # equals (1 + monthly_return), the standard lognormal correction.
    mu = np.log(1 + monthly_return) - 0.5 * monthly_vol**2
    shocks = rng.normal(loc=mu, scale=monthly_vol, size=(params.n_paths, n_months))
    growth_factors = np.exp(shocks)

    for t in range(1, n_months + 1):
        paths[:, t] = paths[:, t - 1] * growth_factors[:, t - 1] + params.monthly_contribution

    percentiles = np.percentile(paths, PERCENTILES, axis=0)
    final_values = paths[:, -1]

    return SimulationResult(
        months=list(range(n_months + 1)),
        p5=percentiles[0].tolist(),
        p25=percentiles[1].tolist(),
        p50=percentiles[2].tolist(),
        p75=percentiles[3].tolist(),
        p95=percentiles[4].tolist(),
        final_mean=float(np.mean(final_values)),
        final_median=float(np.median(final_values)),
        final_p5=float(percentiles[0, -1]),
        final_p95=float(percentiles[4, -1]),
    )
