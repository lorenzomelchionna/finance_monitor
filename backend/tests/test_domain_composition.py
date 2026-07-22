"""Unit tests for value-weighted composition aggregation."""

import pytest

from app.domain.composition import aggregate_composition


def test_value_weighted_across_two_instruments():
    # A worth 300 is 100% US; B worth 100 is 100% Japan.
    weights = {
        1: {"geography": [("US", 1.0)]},
        2: {"geography": [("Japan", 1.0)]},
    }
    values = {1: 300.0, 2: 100.0}
    out = aggregate_composition(weights, values)
    geo = {s.key: s.weight for s in out["geography"]}
    assert geo["US"] == pytest.approx(0.75)
    assert geo["Japan"] == pytest.approx(0.25)
    # Sorted descending.
    assert out["geography"][0].key == "US"


def test_keys_combine_across_instruments():
    weights = {
        1: {"sector": [("Tech", 0.5), ("Financials", 0.5)]},
        2: {"sector": [("Tech", 1.0)]},
    }
    values = {1: 100.0, 2: 100.0}
    out = aggregate_composition(weights, values)
    sec = {s.key: s.weight for s in out["sector"]}
    assert sec["Tech"] == pytest.approx(0.75)  # (100*0.5 + 100*1.0)/200
    assert sec["Financials"] == pytest.approx(0.25)


def test_dimension_only_over_instruments_that_have_it():
    # Only instrument 1 has sector data -> sector aggregates over its
    # value alone, ignoring instrument 2's value.
    weights = {
        1: {"geography": [("US", 1.0)], "sector": [("Tech", 1.0)]},
        2: {"geography": [("Japan", 1.0)]},
    }
    values = {1: 100.0, 2: 100.0}
    out = aggregate_composition(weights, values)
    assert {s.key for s in out["sector"]} == {"Tech"}
    assert out["sector"][0].weight == pytest.approx(1.0)
    geo = {s.key: s.weight for s in out["geography"]}
    assert geo["US"] == pytest.approx(0.5)


def test_empty():
    assert aggregate_composition({}, {}) == {}
