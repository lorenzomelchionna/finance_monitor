"""Pure portfolio valuation math: EUR (base-currency) valuation of
holdings + currency exposure aggregation.

No FastAPI/SQLModel/provider imports — inputs are plain dataclasses
already resolved by the caller (services/portfolio_service.py does the
DB/provider lookups), so this module is unit-testable in isolation and
has no I/O of its own.

v1 scope note: this is snapshot-only. Both current value and cost basis
are converted to the base currency using the *current* FX rate — there
is no historical FX captured at purchase time, so P/L here mixes asset
return and FX return rather than decomposing them. See the plan's
Roadmap for full FX attribution.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HoldingPosition:
    """A holding plus its already-resolved current market data."""

    instrument_id: int
    instrument_name: str
    quantity: float
    avg_cost_price: float
    cost_currency: str
    current_price: float | None  # None => no price available anywhere
    price_currency: str
    price_status: str  # "ok" | "manual" | "missing" — passthrough, informational only


@dataclass(frozen=True)
class PositionValuation:
    instrument_id: int
    instrument_name: str
    quantity: float
    price_currency: str
    price_status: str
    value_base: float | None
    cost_base: float | None
    pnl_base: float | None
    exclusion_reason: str | None  # None | "missing_price" | "missing_fx"


@dataclass(frozen=True)
class PortfolioSummary:
    base_currency: str
    positions: list[PositionValuation]
    total_value_base: float
    total_cost_base: float
    total_pnl_base: float
    currency_exposure: dict[str, float]  # price_currency -> fraction (0..1) of total_value_base


def value_portfolio(
    positions: list[HoldingPosition],
    fx_rates: dict[str, float],
    base_currency: str,
) -> PortfolioSummary:
    """fx_rates maps a currency code to "units of base_currency per 1
    unit of that currency" (base_currency itself needs no entry)."""
    valuations: list[PositionValuation] = []
    total_value = 0.0
    total_cost = 0.0
    exposure_value: dict[str, float] = {}

    for pos in positions:
        if pos.current_price is None:
            valuations.append(
                PositionValuation(
                    instrument_id=pos.instrument_id,
                    instrument_name=pos.instrument_name,
                    quantity=pos.quantity,
                    price_currency=pos.price_currency,
                    price_status=pos.price_status,
                    value_base=None,
                    cost_base=None,
                    pnl_base=None,
                    exclusion_reason="missing_price",
                )
            )
            continue

        price_fx = 1.0 if pos.price_currency == base_currency else fx_rates.get(pos.price_currency)
        cost_fx = 1.0 if pos.cost_currency == base_currency else fx_rates.get(pos.cost_currency)

        if price_fx is None or cost_fx is None:
            valuations.append(
                PositionValuation(
                    instrument_id=pos.instrument_id,
                    instrument_name=pos.instrument_name,
                    quantity=pos.quantity,
                    price_currency=pos.price_currency,
                    price_status=pos.price_status,
                    value_base=None,
                    cost_base=None,
                    pnl_base=None,
                    exclusion_reason="missing_fx",
                )
            )
            continue

        value_base = pos.quantity * pos.current_price * price_fx
        cost_base = pos.quantity * pos.avg_cost_price * cost_fx

        valuations.append(
            PositionValuation(
                instrument_id=pos.instrument_id,
                instrument_name=pos.instrument_name,
                quantity=pos.quantity,
                price_currency=pos.price_currency,
                price_status=pos.price_status,
                value_base=value_base,
                cost_base=cost_base,
                pnl_base=value_base - cost_base,
                exclusion_reason=None,
            )
        )
        total_value += value_base
        total_cost += cost_base
        exposure_value[pos.price_currency] = exposure_value.get(pos.price_currency, 0.0) + value_base

    currency_exposure = (
        {ccy: v / total_value for ccy, v in exposure_value.items()} if total_value > 0 else {}
    )

    return PortfolioSummary(
        base_currency=base_currency,
        positions=valuations,
        total_value_base=total_value,
        total_cost_base=total_cost,
        total_pnl_base=total_value - total_cost,
        currency_exposure=currency_exposure,
    )
