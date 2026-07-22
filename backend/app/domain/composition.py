"""Pure portfolio-level composition aggregation.

Given each instrument's look-through weights (per dimension) and its
current market value, produce the value-weighted portfolio exposure per
dimension. No I/O — inputs are plain dicts assembled by the caller, so
this is unit-testable in isolation.

Per dimension the aggregate spans only the instruments that actually
have data for that dimension; the caller reports coverage (which held
value is missing a breakdown) separately.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightSlice:
    key: str
    weight: float  # 0..1 fraction of the covered value


def aggregate_composition(
    weights_by_instrument: dict[int, dict[str, list[tuple[str, float]]]],
    values: dict[int, float],
) -> dict[str, list[WeightSlice]]:
    """weights_by_instrument: {instrument_id: {dimension: [(key, w), ...]}}.
    values: {instrument_id: market_value}. Returns {dimension: [slices
    sorted desc]}, each dimension normalized to sum ~1 over the value
    that had data for it."""
    # Collect the set of dimensions present anywhere.
    dimensions: set[str] = set()
    for dims in weights_by_instrument.values():
        dimensions.update(dims.keys())

    result: dict[str, list[WeightSlice]] = {}
    for dim in dimensions:
        acc: dict[str, float] = {}
        covered_value = 0.0
        for iid, dims in weights_by_instrument.items():
            if dim not in dims:
                continue
            value = values.get(iid, 0.0)
            if value <= 0:
                continue
            covered_value += value
            for key, w in dims[dim]:
                acc[key] = acc.get(key, 0.0) + value * w
        if covered_value <= 0:
            continue
        slices = [WeightSlice(key=k, weight=v / covered_value) for k, v in acc.items()]
        slices.sort(key=lambda s: s.weight, reverse=True)
        result[dim] = slices
    return result
