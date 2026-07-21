"""Unit tests for the pure portfolio-value aggregation."""

from app.domain.history import actual_portfolio_value, aggregate_portfolio_value


def test_simple_two_instrument_aggregate():
    series = {
        1: [("2020-01-01", 100.0), ("2020-01-02", 110.0)],
        2: [("2020-01-01", 50.0), ("2020-01-02", 60.0)],
    }
    quantities = {1: 2.0, 2: 3.0}
    result = aggregate_portfolio_value(series, quantities)

    assert [p.date for p in result] == ["2020-01-01", "2020-01-02"]
    assert result[0].value == 2 * 100.0 + 3 * 50.0  # 350
    assert result[1].value == 2 * 110.0 + 3 * 60.0  # 400


def test_intersection_start_drops_earlier_dates():
    # Instrument 2 starts a day later -> aggregate begins on 2020-01-02.
    series = {
        1: [("2020-01-01", 100.0), ("2020-01-02", 100.0), ("2020-01-03", 100.0)],
        2: [("2020-01-02", 10.0), ("2020-01-03", 10.0)],
    }
    quantities = {1: 1.0, 2: 1.0}
    result = aggregate_portfolio_value(series, quantities)

    assert [p.date for p in result] == ["2020-01-02", "2020-01-03"]
    assert result[0].value == 110.0


def test_forward_fills_internal_gap():
    # Instrument 2 has no point on 2020-01-02 (e.g. exchange holiday) ->
    # its last close (10) is carried forward.
    series = {
        1: [("2020-01-01", 100.0), ("2020-01-02", 100.0), ("2020-01-03", 100.0)],
        2: [("2020-01-01", 10.0), ("2020-01-03", 20.0)],
    }
    quantities = {1: 1.0, 2: 1.0}
    result = aggregate_portfolio_value(series, quantities)

    by_date = {p.date: p.value for p in result}
    assert by_date["2020-01-02"] == 110.0  # 100 + carried-forward 10
    assert by_date["2020-01-03"] == 120.0


def test_instrument_without_quantity_excluded():
    series = {1: [("2020-01-01", 100.0)], 2: [("2020-01-01", 100.0)]}
    quantities = {1: 1.0}  # no qty for 2
    result = aggregate_portfolio_value(series, quantities)
    assert result[0].value == 100.0


def test_empty_inputs():
    assert aggregate_portfolio_value({}, {}) == []
    assert aggregate_portfolio_value({1: []}, {1: 1.0}) == []


def test_actual_value_reconstructs_held_quantity_over_time():
    # Price constant at 100. Buy 1 share on day 2, another on day 3.
    series = {
        1: [("2025-01-01", 100.0), ("2025-01-02", 100.0), ("2025-01-03", 100.0), ("2025-01-04", 100.0)],
    }
    deltas = {1: [("2025-01-02", 1.0), ("2025-01-03", 1.0)]}
    result = actual_portfolio_value(series, deltas)

    by_date = {p.date: p.value for p in result}
    # Series starts at the first purchase (day 2), not day 1.
    assert result[0].date == "2025-01-02"
    assert by_date["2025-01-02"] == 100.0  # 1 share
    assert by_date["2025-01-03"] == 200.0  # 2 shares
    assert by_date["2025-01-04"] == 200.0  # still 2 shares


def test_actual_value_price_moves_after_purchase():
    series = {1: [("2025-01-01", 100.0), ("2025-01-02", 150.0)]}
    deltas = {1: [("2025-01-01", 2.0)]}
    result = actual_portfolio_value(series, deltas)
    by_date = {p.date: p.value for p in result}
    assert by_date["2025-01-01"] == 200.0
    assert by_date["2025-01-02"] == 300.0  # 2 shares * 150


def test_actual_value_empty_without_deltas():
    assert actual_portfolio_value({1: [("2025-01-01", 100.0)]}, {}) == []


def test_actual_value_start_date_independent_of_delta_order():
    # Deltas passed out of chronological order — series must still start
    # at the earliest purchase, not the first list element.
    series = {1: [("2025-01-01", 100.0), ("2025-01-02", 100.0), ("2025-01-03", 100.0)]}
    deltas = {1: [("2025-01-03", 1.0), ("2025-01-01", 1.0)]}
    result = actual_portfolio_value(series, deltas)
    assert result[0].date == "2025-01-01"
    assert result[0].value == 100.0  # 1 share bought on day 1
