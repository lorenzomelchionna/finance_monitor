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

Two shock distributions are available:

- "normal" — classic GBM: log-returns are Gaussian, so monthly growth
  factors are lognormal. Analytically clean, but it has thin tails and
  therefore *systematically understates crashes*: a −30% month is
  effectively impossible under it, while real equity markets deliver one
  every couple of decades.

- "student_t" — Student-t shocks, standardised to the same volatility.
  Roughly 5 degrees of freedom matches monthly equity returns
  empirically. Same mean and standard deviation as the normal case, but
  far more mass in the tails, so the p5 band reflects the kind of loss
  that actually happens.

Note on why the t branch works in *simple* return space rather than log
space: exp() of a Student-t has no finite mean (its moment generating
function diverges), so the lognormal construction would give an
undefined expected return and a sample mean dominated by a handful of
outliers. Drawing the simple return directly keeps E[r] equal to the
requested figure. The draw is clipped at −100%, which is the real
economic floor for a diversified fund and only binds deep in the tail.

Historical stress-test scenarios (2008/2020/2022) remain a separate,
complementary analysis in the plan's Roadmap.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

PERCENTILES = (5, 25, 50, 75, 95)

Distribution = Literal["normal", "student_t"]

# Monthly equity returns are empirically close to a t with ~4-6 df.
DEFAULT_DF = 5.0


@dataclass(frozen=True)
class SimulationParams:
    seed_capital: float
    monthly_contribution: float
    years: int
    expected_annual_return: float  # e.g. 0.07 for 7%
    annual_volatility: float  # e.g. 0.15 for 15%
    n_paths: int = 10_000
    random_seed: int | None = None
    distribution: Distribution = "student_t"
    # Degrees of freedom for the t. Lower = fatter tails; must exceed 2
    # for the variance (and so the volatility calibration) to exist.
    degrees_of_freedom: float = DEFAULT_DF


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
    # Share of paths ending below the cash actually paid in. Thin-tailed
    # models put this near zero over long horizons; it's the number fat
    # tails move most, so it's worth surfacing rather than inferring.
    prob_below_contributed: float
    total_contributed: float
    # Worst peak-to-trough fall of the market index along each path,
    # summarised across paths. Terminal wealth barely notices fat tails
    # over a long horizon (240 monthly shocks average out towards a
    # normal), but the drawdown *endured on the way* is exactly where
    # they show up — and it's the loss an investor actually feels.
    median_max_drawdown: float
    worst_max_drawdown: float  # 95th percentile of the per-path maximum


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

    # A t with `df` degrees of freedom has variance df/(df-2), so scaling
    # by the reciprocal square root gives unit variance and lets the same
    # `monthly_vol` mean the same thing under both distributions.
    df = params.degrees_of_freedom
    use_t = params.distribution == "student_t"
    if use_t and df <= 2:
        raise ValueError("degrees_of_freedom must be > 2 for the variance to exist")
    t_scale = float(np.sqrt((df - 2.0) / df)) if use_t else 1.0

    # Shocks are drawn one month at a time into a reusable (n_paths,)
    # buffer rather than materialising two full (n_paths, n_months)
    # matrices. Same maths, but peak memory drops from ~3 large arrays to
    # 1 — and since CPython rarely returns freed heap to the OS, that peak
    # would otherwise stay resident (and billable) for the process' life.
    # Drawdown is tracked on a pure market index (no contributions), so
    # it measures the fall in what's invested rather than being masked by
    # fresh cash arriving each month. Running peak/max keeps memory flat
    # — no need to retain the whole index path.
    index = np.ones(params.n_paths)
    peak = np.ones(params.n_paths)
    max_dd = np.zeros(params.n_paths)
    drawdown = np.empty(params.n_paths)

    step = np.empty(params.n_paths)
    for t in range(1, n_months + 1):
        if use_t:
            # Simple return: mean `monthly_return`, sd `monthly_vol`,
            # floored at -100% (a fund can't be worth less than nothing).
            step[:] = rng.standard_t(df, size=params.n_paths)
            step *= monthly_vol * t_scale
            step += monthly_return
            np.maximum(step, -1.0, out=step)
            step += 1.0
        else:
            rng.standard_normal(params.n_paths, out=step)
            step *= monthly_vol
            step += mu
            np.exp(step, out=step)
        paths[:, t] = paths[:, t - 1] * step + params.monthly_contribution

        index *= step
        np.maximum(peak, index, out=peak)
        np.divide(index, peak, out=drawdown)
        np.subtract(1.0, drawdown, out=drawdown)
        np.maximum(max_dd, drawdown, out=max_dd)

    percentiles = np.percentile(paths, PERCENTILES, axis=0)
    final_values = paths[:, -1]
    total_contributed = params.seed_capital + params.monthly_contribution * n_months

    return SimulationResult(
        prob_below_contributed=float(np.mean(final_values < total_contributed)),
        total_contributed=float(total_contributed),
        median_max_drawdown=float(np.median(max_dd)),
        worst_max_drawdown=float(np.percentile(max_dd, 95)),
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
