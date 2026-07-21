"""Unit tests for the pure portfolio-value aggregation."""

from app.domain.history import aggregate_portfolio_value


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
