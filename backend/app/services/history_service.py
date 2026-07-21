"""Orchestrates historical price series: provider fetch + portfolio
aggregation.

Seam between `providers/` (network history) and `api/`. The pure
aggregation math lives in `domain/history.py`; this module only handles
DB reads, provider calls, currency filtering and result shaping.
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.config import get_settings
from app.domain.history import aggregate_portfolio_value
from app.models.holding import Holding
from app.models.instrument import Instrument
from app.providers.registry import resolve_history


def get_portfolio_history(session: Session) -> dict:
    """Full available daily history for every held instrument, plus the
    aggregate portfolio value series. Non-base-currency instruments are
    charted individually but excluded from the aggregate (no FX-history
    support yet — see Roadmap) with a warning."""
    settings = get_settings()
    base_currency = settings.base_currency

    holdings = session.exec(select(Holding)).all()
    quantities: dict[int, float] = defaultdict(float)
    for h in holdings:
        quantities[h.instrument_id] += h.quantity

    instruments = {
        i.id: i
        for i in session.exec(select(Instrument)).all()
        if i.id in quantities
    }

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
        series_out.append(
            {
                "instrument_id": iid,
                "name": instrument.name,
                "ticker": instrument.ticker,
                "currency": instrument.currency,
                "points": [{"date": d, "close": c} for d, c in pairs],
            }
        )

        if instrument.currency == base_currency:
            aggregate_input[iid] = pairs
        else:
            warnings.append(
                f"{instrument.name}: quotato in {instrument.currency}, escluso dall'aggregato "
                f"(conversione storica {instrument.currency}->{base_currency} non ancora supportata)."
            )

    aggregate = aggregate_portfolio_value(aggregate_input, quantities)

    return {
        "base_currency": base_currency,
        "series": series_out,
        "portfolio": [{"date": vp.date, "value": vp.value} for vp in aggregate],
        "warnings": warnings,
    }
