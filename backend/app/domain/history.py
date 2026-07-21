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


def actual_portfolio_value(
    series_by_instrument: dict[int, list[tuple[str, float]]],
    deltas_by_instrument: dict[int, list[tuple[str, float]]],
) -> list[ValuePoint]:
    """Actual portfolio value over time, reconstructing the quantity
    *actually held* on each date from the transaction ledger (buys add,
    sells subtract). Unlike aggregate_portfolio_value (which values a
    fixed current basket backwards), this starts at the first purchase
    and grows with each contribution + market move — so it lines up with
    the cumulative-invested series for an honest "invested vs value"
    view.

    deltas_by_instrument: {instrument_id: [(iso_date, signed_qty), ...]},
    buy = +qty, sell = -qty. Only instruments present in both maps
    contribute. Prices are forward-filled from each instrument's last
    known close."""
    included = {
        iid: series
        for iid, series in series_by_instrument.items()
        if series and iid in deltas_by_instrument and deltas_by_instrument[iid]
    }
    if not included:
        return []

    # Start at the earliest purchase across the portfolio (min over all
    # delta dates — the passed lists are not assumed sorted).
    start_date = min(
        d for iid in included for (d, _) in deltas_by_instrument[iid]
    )

    price_lookup = {iid: dict(series) for iid, series in included.items()}
    all_dates = sorted(
        {d for series in included.values() for (d, _) in series if d >= start_date}
    )

    # Pre-sort deltas per instrument for a forward sweep.
    deltas_sorted = {
        iid: sorted(deltas_by_instrument[iid], key=lambda x: x[0]) for iid in included
    }
    delta_idx = {iid: 0 for iid in included}
    held_qty = {iid: 0.0 for iid in included}
    last_close = {iid: 0.0 for iid in included}

    result: list[ValuePoint] = []
    for date in all_dates:
        total = 0.0
        for iid in included:
            # Advance the held quantity by any trades on/before this date.
            ds = deltas_sorted[iid]
            while delta_idx[iid] < len(ds) and ds[delta_idx[iid]][0] <= date:
                held_qty[iid] += ds[delta_idx[iid]][1]
                delta_idx[iid] += 1
            if date in price_lookup[iid]:
                last_close[iid] = price_lookup[iid][date]
            total += held_qty[iid] * last_close[iid]
        result.append(ValuePoint(date=date, value=total))
    return result


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
