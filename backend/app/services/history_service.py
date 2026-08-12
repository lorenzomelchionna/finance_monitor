"""Orchestrates historical price series: provider fetch + portfolio
aggregation.

Seam between `providers/` (network history) and `api/`. The pure
aggregation math lives in `domain/history.py`; this module only handles
DB reads, provider calls, currency filtering and result shaping.
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.config import get_settings
from app.domain.history import actual_portfolio_value, aggregate_portfolio_value
from app.domain.performance import TxnLike, cumulative_invested
from app.models.transaction import Transaction
from app.providers.registry import resolve_history
from app.services.positions_service import get_positions


def get_portfolio_history(session: Session) -> dict:
    """Full available daily history for every held instrument, plus the
    aggregate portfolio value series. Non-base-currency instruments are
    charted individually but excluded from the aggregate (no FX-history
    support yet — see Roadmap) with a warning."""
    settings = get_settings()
    base_currency = settings.base_currency

    derived = get_positions(session)
    quantities: dict[int, float] = {p.instrument.id: p.quantity for p in derived}
    instruments = {p.instrument.id: p.instrument for p in derived}

    all_txn_likes = [
        TxnLike(
            instrument_id=t.instrument_id,
            trade_date=t.trade_date,
            sign=t.sign.value,
            quantity=t.quantity,
            price=t.price,
            gross_amount=t.gross_amount,
            commissions=t.commissions,
        )
        for t in session.exec(select(Transaction)).all()
    ]
    txns_by_instrument: dict[int, list[TxnLike]] = defaultdict(list)
    for t in all_txn_likes:
        txns_by_instrument[t.instrument_id].append(t)

    series_out: list[dict] = []
    warnings: list[str] = []
    aggregate_input: dict[int, list[tuple[str, float]]] = {}

    for iid, instrument in instruments.items():
        points = resolve_history(instrument, settings.default_price_provider)
        if points is None:
            warnings.append(
                f"{instrument.name}: nessuno storico disponibile (ticker '{instrument.ticker}' non risolto)."
            )
            continue
        if not points:
            warnings.append(f"{instrument.name}: storico vuoto.")
            continue

        pairs = [(p.date, p.close) for p in points]
        instrument_txns = txns_by_instrument.get(iid, [])
        # No ledger for this instrument (e.g. manual-price-only holding) ->
        # leave invested unset rather than a misleading flat 0.0.
        invested_series: list[float | None] = (
            cumulative_invested(instrument_txns, [d for d, _ in pairs])
            if instrument_txns
            else [None] * len(pairs)
        )
        # Position value (held qty * close) for this instrument alone —
        # comparable to `invested` for a gain %. `close` itself is a
        # per-unit price and NOT comparable to total € invested (dividing
        # one by the other produces nonsense like -90%). Reuses
        # actual_portfolio_value with a single-instrument input; it
        # naturally returns nothing before the first purchase.
        instrument_deltas = [
            (t.trade_date.isoformat(), t.quantity if t.sign == "A" else -t.quantity)
            for t in instrument_txns
        ]
        position_value_by_date: dict[str, float] = (
            {vp.date: vp.value for vp in actual_portfolio_value({iid: pairs}, {iid: instrument_deltas})}
            if instrument_deltas
            else {}
        )
        series_out.append(
            {
                "instrument_id": iid,
                "name": instrument.name,
                "ticker": instrument.ticker,
                "currency": instrument.currency,
                "points": [
                    {
                        "date": d,
                        "close": c,
                        "invested": inv,
                        "position_value": position_value_by_date.get(d),
                    }
                    for (d, c), inv in zip(pairs, invested_series)
                ],
            }
        )

        if instrument.currency == base_currency:
            aggregate_input[iid] = pairs
        else:
            warnings.append(
                f"{instrument.name}: quotato in {instrument.currency}, escluso dall'aggregato "
                f"(conversione storica {instrument.currency}->{base_currency} non ancora supportata)."
            )

    aggregated_ids = set(aggregate_input.keys())
    txn_likes = [t for t in all_txn_likes if t.instrument_id in aggregated_ids]

    # With a ledger available, reconstruct the *actual* value over time
    # (quantity held at each date) so it lines up with cumulative
    # invested. Without transactions, fall back to valuing the fixed
    # current basket backwards.
    deltas_by_instrument: dict[int, list[tuple[str, float]]] = defaultdict(list)
    for t in txn_likes:
        signed = t.quantity if t.sign == "A" else -t.quantity
        deltas_by_instrument[t.instrument_id].append((t.trade_date.isoformat(), signed))

    if deltas_by_instrument:
        aggregate = actual_portfolio_value(aggregate_input, dict(deltas_by_instrument))
    else:
        aggregate = aggregate_portfolio_value(aggregate_input, quantities)

    # Cumulative invested capital aligned to the aggregate's dates.
    aggregate_dates = [vp.date for vp in aggregate]
    invested = cumulative_invested(txn_likes, aggregate_dates)

    return {
        "base_currency": base_currency,
        "series": series_out,
        "portfolio": [
            {"date": vp.date, "value": vp.value, "invested": inv}
            for vp, inv in zip(aggregate, invested)
        ],
        "warnings": warnings,
    }
