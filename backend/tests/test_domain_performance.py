"""Unit tests for cost basis, XIRR and cumulative-invested math."""

from datetime import date

import pytest

from app.domain.performance import (
    CostBasis,
    TxnLike,
    cost_basis_by_instrument,
    cumulative_invested,
    xirr,
)


def _buy(iid, d, qty, price, comm=0.0):
    return TxnLike(iid, d, "A", qty, price, qty * price, comm)


def test_cost_basis_weighted_average_with_commissions():
    txns = [
        _buy(1, date(2025, 1, 1), 10, 100.0, comm=5.0),
        _buy(1, date(2025, 2, 1), 10, 120.0, comm=5.0),
    ]
    cb = cost_basis_by_instrument(txns)[1]
    # invested = 1000+5 + 1200+5 = 2210 over 20 units
    assert cb.quantity == 20
    assert cb.invested == pytest.approx(2210.0)
    assert cb.avg_cost == pytest.approx(110.5)
    assert cb.commissions == pytest.approx(10.0)


def test_cost_basis_sell_reduces_invested_at_average():
    txns = [
        _buy(1, date(2025, 1, 1), 10, 100.0),
        TxnLike(1, date(2025, 3, 1), "V", 4, 150.0, 600.0, 0.0),
    ]
    cb = cost_basis_by_instrument(txns)[1]
    assert cb.quantity == 6
    assert cb.invested == pytest.approx(600.0)  # 1000 - 4*100
    assert cb.avg_cost == pytest.approx(100.0)


def test_xirr_simple_one_year_double():
    # -100 today, +110 one year later -> ~10%.
    flows = [(date(2025, 1, 1), -100.0), (date(2026, 1, 1), 110.0)]
    r = xirr(flows)
    assert r == pytest.approx(0.10, abs=1e-3)


def test_xirr_needs_both_signs():
    assert xirr([(date(2025, 1, 1), -100.0), (date(2026, 1, 1), -50.0)]) is None
    assert xirr([(date(2025, 1, 1), -100.0)]) is None


def test_xirr_multiple_contributions_positive_return():
    flows = [
        (date(2025, 1, 1), -100.0),
        (date(2025, 6, 1), -100.0),
        (date(2026, 1, 1), 230.0),
    ]
    r = xirr(flows)
    assert r is not None and r > 0


def test_cumulative_invested_steps_on_trade_dates():
    txns = [
        _buy(1, date(2025, 1, 2), 1, 100.0, comm=1.0),
        _buy(1, date(2025, 1, 4), 1, 200.0),
    ]
    dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]
    inv = cumulative_invested(txns, dates)
    assert inv == [0.0, 101.0, 101.0, 301.0, 301.0]
