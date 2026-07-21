"""Pure portfolio-value-over-time aggregation.

No web, no DB, no yfinance — takes already-fetched per-instrument close
series plus the held quantities and produces a single portfolio value
series. Kept here (not in a service) so the aggregation logic is unit-
testable in isolation.

Design notes:
- The aggregate spans from the *latest* first-date across the included
  instruments (intersection start). Extending earlier would sum an
  incomplete basket and draw a misleading jump when a younger
  instrument's history begins. The single-instrument series (served
  straight from the provider) still shows each one's full history.
- Internal gaps (an instrument not trading on a day another did, e.g.
  differing exchange holidays) are forward-filled from that
  instrument's last known close.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValuePoint:
    date: str
    value: float


def aggregate_portfolio_value(
    series_by_instrument: dict[int, list[tuple[str, float]]],
    quantities: dict[int, float],
) -> list[ValuePoint]:
    """series_by_instrument: {instrument_id: [(iso_date, close), ...]}
    (each already sorted ascending by date). quantities: {instrument_id:
    qty}. Only instruments present in both maps with a non-empty series
    contribute."""
    included = {
        iid: series
        for iid, series in series_by_instrument.items()
        if series and iid in quantities
    }
    if not included:
        return []

    # Intersection start: the aggregate begins only once every included
    # instrument has data, so the basket is always complete.
    start_date = max(series[0][0] for series in included.values())

    lookup: dict[int, dict[str, float]] = {
        iid: dict(series) for iid, series in included.items()
    }
    all_dates = sorted(
        {d for series in included.values() for (d, _) in series if d >= start_date}
    )

    last_close: dict[int, float] = {}
    result: list[ValuePoint] = []
    for date in all_dates:
        total = 0.0
        for iid, series_lookup in lookup.items():
            if date in series_lookup:
                last_close[iid] = series_lookup[date]
            # After start_date every instrument has a prior close, so
            # forward-fill always has a value.
            total += quantities[iid] * last_close.get(iid, 0.0)
        result.append(ValuePoint(date=date, value=total))
    return result
