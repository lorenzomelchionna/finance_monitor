"""Sanity tests for the v1 data model: insert one row per table and
verify relationships resolve. Not exhaustive constraint testing — just
confirms the schema is usable end-to-end from Python.
"""

from datetime import date

from app.models.breakdown import BreakdownDimension, CompositionBreakdown
from app.models.instrument import AssetClass, Instrument
from app.models.price import PriceSnapshot, PriceSource
from app.models.transaction import Transaction, TransactionSign


def test_insert_instrument_transaction_price_and_breakdown(session):
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

    transaction = Transaction(
        instrument_id=instrument.id,
        isin=instrument.isin,
        name=instrument.name,
        trade_date=date(2025, 8, 18),
        sign=TransactionSign.buy,
        quantity=10,
        currency="EUR",
        price=95.5,
        gross_amount=955.0,
        dedup_key="test-key-1",
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
    session.add_all([transaction, price, breakdown])
    session.commit()

    session.refresh(transaction)
    session.refresh(price)
    session.refresh(breakdown)

    assert transaction.instrument_id == instrument.id
    assert transaction.sign == TransactionSign.buy
    assert price.source == PriceSource.manual
    assert breakdown.weight == 0.62
    # New instruments are counted towards the portfolio unless excluded.
    assert instrument.included is True
