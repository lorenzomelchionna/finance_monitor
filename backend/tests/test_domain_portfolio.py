"""Unit tests for domain/portfolio.py — pure math, no DB/network. This
is the module the plan calls out as independently testable financial
logic."""

import pytest

from app.domain.portfolio import HoldingPosition, value_portfolio


def test_single_position_same_currency_as_base():
    positions = [
        HoldingPosition(
            instrument_id=1,
            instrument_name="VWCE",
            quantity=10,
            avg_cost_price=90.0,
            cost_currency="EUR",
            current_price=100.0,
            price_currency="EUR",
            price_status="ok",
        )
    ]

    summary = value_portfolio(positions, fx_rates={}, base_currency="EUR")

    assert summary.total_value_base == 1000.0
    assert summary.total_cost_base == 900.0
    assert summary.total_pnl_base == 100.0
    assert summary.currency_exposure == {"EUR": 1.0}
    assert summary.positions[0].exclusion_reason is None


def test_position_in_foreign_currency_converted_via_fx():
    positions = [
        HoldingPosition(
            instrument_id=2,
            instrument_name="AAPL",
            quantity=2,
            avg_cost_price=100.0,
            cost_currency="USD",
            current_price=150.0,
            price_currency="USD",
            price_status="manual",
        )
    ]

    # 1 USD = 0.9 EUR
    summary = value_portfolio(positions, fx_rates={"USD": 0.9}, base_currency="EUR")

    assert summary.total_value_base == pytest.approx(2 * 150.0 * 0.9)
    assert summary.total_cost_base == pytest.approx(2 * 100.0 * 0.9)
    assert summary.currency_exposure == {"USD": 1.0}


def test_missing_price_excludes_position_from_totals():
    positions = [
        HoldingPosition(
            instrument_id=3,
            instrument_name="Illiquid",
            quantity=5,
            avg_cost_price=10.0,
            cost_currency="EUR",
            current_price=None,
            price_currency="EUR",
            price_status="missing",
        )
    ]

    summary = value_portfolio(positions, fx_rates={}, base_currency="EUR")

    assert summary.total_value_base == 0.0
    assert summary.positions[0].exclusion_reason == "missing_price"


def test_missing_fx_excludes_position_but_keeps_it_listed():
    positions = [
        HoldingPosition(
            instrument_id=4,
            instrument_name="JPY fund",
            quantity=1,
            avg_cost_price=1000.0,
            cost_currency="JPY",
            current_price=1200.0,
            price_currency="JPY",
            price_status="ok",
        )
    ]

    # No JPY rate supplied -> excluded, but still present in `positions`.
    summary = value_portfolio(positions, fx_rates={}, base_currency="EUR")

    assert summary.positions[0].exclusion_reason == "missing_fx"
    assert summary.total_value_base == 0.0
    assert len(summary.positions) == 1


def test_currency_exposure_split_across_multiple_currencies():
    positions = [
        HoldingPosition(5, "EUR fund", 10, 90.0, "EUR", 100.0, "EUR", "ok"),
        HoldingPosition(6, "USD fund", 10, 90.0, "USD", 100.0, "USD", "ok"),
    ]

    summary = value_portfolio(positions, fx_rates={"USD": 1.0}, base_currency="EUR")

    assert summary.total_value_base == 2000.0
    assert summary.currency_exposure == {"EUR": 0.5, "USD": 0.5}
