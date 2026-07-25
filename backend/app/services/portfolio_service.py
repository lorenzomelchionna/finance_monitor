"""Read-side orchestration for the portfolio summary: derives positions
from the transaction ledger, pulls the latest known prices, resolves the
FX rates needed to convert every currency in play to the base currency,
then hands everything to domain.portfolio (pure math, no DB/provider
access).

Deliberately does NOT trigger a fresh price fetch — it uses whatever is
already stored (last refresh via /api/prices/refresh or a manual entry).
Loading the dashboard should be fast and not depend on network/provider
availability.
"""

from datetime import date

from sqlmodel import Session

from app.config import get_settings
from app.domain.performance import TxnLike, xirr
from app.domain.portfolio import HoldingPosition, PortfolioSummary, value_portfolio
from app.models.price import PriceSource
from app.providers.registry import resolve_fx_rate
from app.services.positions_service import get_positions, load_txn_likes
from app.services.pricing_service import get_latest_price


def get_portfolio_summary(session: Session) -> PortfolioSummary:
    settings = get_settings()
    base = settings.base_currency

    # Positions come from the ledger — quantity and cost are never
    # hand-entered, so they cannot drift from what was actually traded.
    derived = get_positions(session)

    txns_by_instrument: dict[int, list[TxnLike]] = {}
    for t in load_txn_likes(session):
        txns_by_instrument.setdefault(t.instrument_id, []).append(t)

    # Resolve FX up front so we can value positions (needed for XIRR's
    # final synthetic inflow) before handing off to the domain.
    currencies_needed = {base} | {p.instrument.currency for p in derived}
    fx_rates: dict[str, float] = {}
    for currency in currencies_needed:
        if currency == base:
            continue
        rate = resolve_fx_rate(currency, base, settings.default_price_provider)
        if rate is not None:
            fx_rates[currency] = rate

    today = date.today()
    positions: list[HoldingPosition] = []
    all_flows: list[tuple[date, float]] = []
    total_value_base = 0.0

    for pos in derived:
        instrument = pos.instrument
        snapshot = get_latest_price(session, instrument.id)

        if snapshot is not None:
            current_price = snapshot.price
            price_currency = snapshot.currency
            price_status = "ok" if snapshot.source == PriceSource.yfinance else "manual"
        else:
            current_price = None
            price_currency = instrument.currency
            price_status = "missing"

        # Per-instrument money-weighted return: its buys (outflows) plus
        # today's market value (a synthetic inflow).
        position_xirr = None
        instrument_txns = txns_by_instrument.get(instrument.id, [])
        if current_price is not None:
            price_fx = 1.0 if price_currency == base else fx_rates.get(price_currency)
            if price_fx is not None:
                value_base = pos.quantity * current_price * price_fx
                total_value_base += value_base
                if instrument_txns:
                    flows = [
                        (t.trade_date, -(t.gross_amount + t.commissions) if t.sign == "A" else t.gross_amount)
                        for t in instrument_txns
                    ]
                    flows.append((today, value_base))
                    all_flows.extend(flows)
                    position_xirr = xirr(flows)

        positions.append(
            HoldingPosition(
                instrument_id=instrument.id,
                instrument_name=instrument.name,
                quantity=pos.quantity,
                avg_cost_price=pos.avg_cost,
                # Ledger amounts are recorded in the base currency.
                cost_currency=base,
                current_price=current_price,
                price_currency=price_currency,
                price_status=price_status,
                avg_cost_source="transactions",
                xirr=position_xirr,
            )
        )

    # Portfolio-level XIRR from every buy flow plus the total current
    # value as one final inflow today.
    portfolio_xirr = None
    if all_flows and total_value_base > 0:
        buy_flows = [(d, a) for (d, a) in all_flows if a < 0]
        buy_flows.append((today, total_value_base))
        portfolio_xirr = xirr(buy_flows)

    return value_portfolio(positions, fx_rates, base, portfolio_xirr=portfolio_xirr)
