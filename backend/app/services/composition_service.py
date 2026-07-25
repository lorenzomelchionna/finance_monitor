"""Orchestrates look-through composition: provider fetch + persistence +
value-weighted portfolio aggregation.

Persisted rows (CompositionBreakdown) are the source of truth for the
aggregated view; the JustETF provider only populates the `api`-sourced
rows on demand. Manual rows (source="manual") are a fallback the user
can enter when a fetch fails — aggregation reads whatever is stored,
preferring the freshest per (instrument, dimension).
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.config import get_settings
from app.domain.composition import aggregate_composition
from app.models.breakdown import BreakdownDimension, BreakdownSource, CompositionBreakdown
from app.models.instrument import Instrument
from app.providers.registry import resolve_composition
from app.services.portfolio_service import get_portfolio_summary
from app.services.positions_service import get_positions


def _held_instruments(session: Session) -> dict[int, Instrument]:
    return {p.instrument.id: p.instrument for p in get_positions(session)}


def refresh_composition(session: Session) -> dict:
    """Fetch geo/sector breakdowns for every held instrument and replace
    the stored `api` rows. Returns per-instrument outcome."""
    settings = get_settings()
    instruments = _held_instruments(session)

    updated: list[str] = []
    failed: list[str] = []

    for iid, instrument in instruments.items():
        breakdowns = resolve_composition(instrument, settings.default_composition_provider)
        if not breakdowns:
            failed.append(instrument.name)
            continue

        # Replace this instrument's api rows wholesale.
        existing = session.exec(
            select(CompositionBreakdown).where(
                CompositionBreakdown.instrument_id == iid,
                CompositionBreakdown.source == BreakdownSource.api,
            )
        ).all()
        for row in existing:
            session.delete(row)

        for dim_str, weights in breakdowns.items():
            dimension = BreakdownDimension(dim_str)
            for w in weights:
                session.add(
                    CompositionBreakdown(
                        instrument_id=iid,
                        dimension=dimension,
                        key=w.key,
                        weight=w.weight,
                        source=BreakdownSource.api,
                    )
                )
        updated.append(instrument.name)

    session.commit()
    return {"updated": updated, "failed": failed}


def get_composition(session: Session) -> dict:
    """Value-weighted portfolio exposure per dimension, from stored
    breakdowns and current position values. Reports which held value has
    no breakdown data (coverage)."""
    instruments = _held_instruments(session)

    # Current market value per instrument, from the portfolio summary.
    summary = get_portfolio_summary(session)
    values: dict[int, float] = {
        p.instrument_id: p.value_base for p in summary.positions if p.value_base is not None
    }
    total_value = sum(values.values())

    # Stored breakdowns grouped by instrument -> dimension -> [(key, w)].
    rows = session.exec(select(CompositionBreakdown)).all()
    weights_by_instrument: dict[int, dict[str, list[tuple[str, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows:
        if r.instrument_id in instruments:
            weights_by_instrument[r.instrument_id][r.dimension.value].append((r.key, r.weight))

    aggregated = aggregate_composition(
        {iid: dict(dims) for iid, dims in weights_by_instrument.items()}, values
    )

    # Coverage per dimension: fraction of portfolio value that had data.
    dimensions = {"geography", "sector"}
    coverage: dict[str, float] = {}
    missing: dict[str, list[str]] = {}
    for dim in dimensions:
        covered = sum(
            values.get(iid, 0.0)
            for iid, dims in weights_by_instrument.items()
            if dim in dims
        )
        coverage[dim] = (covered / total_value) if total_value > 0 else 0.0
        missing[dim] = [
            instruments[iid].name
            for iid in instruments
            if iid in values and dim not in weights_by_instrument.get(iid, {})
        ]

    # Per-instrument breakdowns (for the single-ETF view). Weights sorted
    # desc within each dimension.
    instruments_out = []
    for iid, instrument in instruments.items():
        dims = weights_by_instrument.get(iid)
        if not dims:
            continue
        instruments_out.append(
            {
                "instrument_id": iid,
                "name": instrument.name,
                "ticker": instrument.ticker,
                "dimensions": {
                    dim: [
                        {"key": k, "weight": w}
                        for k, w in sorted(pairs, key=lambda kv: kv[1], reverse=True)
                    ]
                    for dim, pairs in dims.items()
                },
            }
        )
    instruments_out.sort(key=lambda x: values.get(x["instrument_id"], 0.0), reverse=True)

    return {
        "dimensions": {
            dim: [{"key": s.key, "weight": s.weight} for s in slices]
            for dim, slices in aggregated.items()
        },
        "coverage": coverage,
        "missing": missing,
        "instruments": instruments_out,
    }
