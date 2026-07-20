"""Read-side orchestration for the portfolio summary: pulls holdings +
latest known prices from the DB, resolves the FX rates needed to
convert every currency in play to the base currency, then hands
everything to domain.portfolio (pure math, no DB/provider access).

Deliberately does NOT trigger a fresh price fetch — it uses whatever is
already stored (last refresh via /api/prices/refresh or a manual entry).
Loading the dashboard should be fast and not depend on network/provider
availability.
"""

from sqlmodel import Session, select

from app.config import get_settings
from app.domain.portfolio import HoldingPosition, PortfolioSummary, value_portfolio
from app.models.holding import Holding
from app.models.instrument import Instrument
from app.models.price import PriceSource
from app.providers.registry import resolve_fx_rate
from app.services.pricing_service import get_latest_price


def get_portfolio_summary(session: Session) -> PortfolioSummary:
    settings = get_settings()
    holdings = session.exec(select(Holding)).all()

    positions: list[HoldingPosition] = []
    currencies_needed: set[str] = set()

    for holding in holdings:
        instrument = session.get(Instrument, holding.instrument_id)
        snapshot = get_latest_price(session, holding.instrument_id)

        if snapshot is not None:
            current_price = snapshot.price
            price_currency = snapshot.currency
            # Reuse the same ok/manual/missing vocabulary as
            # /api/prices/refresh — the dashboard shouldn't need to know
            # which specific provider ("yfinance") served the price.
            price_status = "ok" if snapshot.source == PriceSource.yfinance else "manual"
        else:
            current_price = None
            price_currency = instrument.currency
            price_status = "missing"

        positions.append(
            HoldingPosition(
                instrument_id=instrument.id,
                instrument_name=instrument.name,
                quantity=holding.quantity,
                avg_cost_price=holding.avg_cost_price,
                cost_currency=holding.cost_currency,
                current_price=current_price,
                price_currency=price_currency,
                price_status=price_status,
            )
        )
        currencies_needed.add(price_currency)
        currencies_needed.add(holding.cost_currency)

    fx_rates: dict[str, float] = {}
    for currency in currencies_needed:
        if currency == settings.base_currency:
            continue
        rate = resolve_fx_rate(currency, settings.base_currency, settings.default_price_provider)
        if rate is not None:
            fx_rates[currency] = rate

    return value_portfolio(positions, fx_rates, settings.base_currency)
