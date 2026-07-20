"""Sanity tests for the v1 data model: insert one row per table and
verify relationships resolve. Not exhaustive constraint testing — just
confirms the schema is usable end-to-end from Python.
"""

from app.models.breakdown import BreakdownDimension, CompositionBreakdown
from app.models.holding import Holding
from app.models.instrument import AssetClass, Instrument
from app.models.price import PriceSnapshot, PriceSource


def test_insert_instrument_holding_price_and_breakdown(session):
    instrument = Instrument(
        isin="IE00BK5BQT80",
        ticker="VWCE.DE",
        name="Vanguard FTSE All-World UCITS ETF",
        currency="EUR",
        asset_class=AssetClass.etf,
    )
    session.add(instrument)
    session.commit()
    session.refresh(instrument)
    assert instrument.id is not None

    holding = Holding(
        instrument_id=instrument.id,
        quantity=10,
        avg_cost_price=95.5,
        cost_currency="EUR",
    )
    price = PriceSnapshot(
        instrument_id=instrument.id,
        price=110.2,
        currency="EUR",
        source=PriceSource.manual,
    )
    breakdown = CompositionBreakdown(
        instrument_id=instrument.id,
        dimension=BreakdownDimension.geography,
        key="US",
        weight=0.62,
    )
    session.add_all([holding, price, breakdown])
    session.commit()

    session.refresh(holding)
    session.refresh(price)
    session.refresh(breakdown)

    assert holding.instrument_id == instrument.id
    assert price.source == PriceSource.manual
    assert breakdown.weight == 0.62
