"""Unit tests for domain/simulation.py — pure numpy, no DB/network.
Covers reproducibility, percentile ordering, and sanity checks against
deterministic (zero-volatility) compounding."""

import pytest

from app.domain.simulation import SimulationParams, run_montecarlo


def test_reproducible_with_same_seed():
    params = SimulationParams(
        seed_capital=10_000,
        monthly_contribution=200,
        years=10,
        expected_annual_return=0.07,
        annual_volatility=0.15,
        n_paths=500,
        random_seed=42,
    )

    result_a = run_montecarlo(params)
    result_b = run_montecarlo(params)

    assert result_a.p50 == result_b.p50
    assert result_a.final_mean == result_b.final_mean


def test_different_seeds_give_different_results():
    base = dict(
        seed_capital=10_000,
        monthly_contribution=200,
        years=10,
        expected_annual_return=0.07,
        annual_volatility=0.15,
        n_paths=500,
    )

    result_a = run_montecarlo(SimulationParams(**base, random_seed=1))
    result_b = run_montecarlo(SimulationParams(**base, random_seed=2))

    assert result_a.final_mean != result_b.final_mean


def test_percentiles_are_monotonic_at_every_month():
    params = SimulationParams(
        seed_capital=5_000,
        monthly_contribution=100,
        years=5,
        expected_annual_return=0.06,
        annual_volatility=0.2,
        n_paths=1_000,
        random_seed=7,
    )

    result = run_montecarlo(params)

    for p5, p25, p50, p75, p95 in zip(result.p5, result.p25, result.p50, result.p75, result.p95):
        assert p5 <= p25 <= p50 <= p75 <= p95


def test_output_length_matches_horizon_in_months():
    params = SimulationParams(
        seed_capital=1_000,
        monthly_contribution=50,
        years=3,
        expected_annual_return=0.05,
        annual_volatility=0.1,
        n_paths=200,
        random_seed=1,
    )

    result = run_montecarlo(params)

    assert len(result.months) == 3 * 12 + 1
    assert len(result.p50) == 3 * 12 + 1
    assert result.months[0] == 0
    assert result.months[-1] == 36


def test_zero_volatility_matches_deterministic_compounding():
    """With sigma=0, every path is identical and equals the closed-form
    compound-growth-plus-contributions formula."""
    monthly_return = (1.06) ** (1 / 12) - 1
    params = SimulationParams(
        seed_capital=1_000,
        monthly_contribution=100,
        years=2,
        expected_annual_return=0.06,
        annual_volatility=0.0,
        n_paths=10,
        random_seed=0,
    )

    result = run_montecarlo(params)

    expected = 1_000.0
    for _ in range(24):
        expected = expected * (1 + monthly_return) + 100

    assert result.p50[-1] == pytest.approx(expected, rel=1e-9)
    # No dispersion at all when volatility is zero.
    assert result.p5[-1] == pytest.approx(result.p95[-1], rel=1e-9)


def test_zero_contribution_and_zero_return_keeps_capital_flat():
    params = SimulationParams(
        seed_capital=2_000,
        monthly_contribution=0,
        years=1,
        expected_annual_return=0.0,
        annual_volatility=0.0,
        n_paths=10,
        random_seed=0,
    )

    result = run_montecarlo(params)

    assert result.p50[0] == pytest.approx(2_000.0)
    assert result.p50[-1] == pytest.approx(2_000.0)
