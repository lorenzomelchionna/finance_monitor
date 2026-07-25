"""Persistence + linking for imported transactions.

Seam between the pure Fineco parser and the DB. The export is the source
of truth for the portfolio: every ISIN it mentions becomes an Instrument
(created on first sight), and positions are derived from these rows —
nothing is entered by hand. The user then chooses which instruments to
count via `Instrument.included`.

The export carries only ISIN and the broker's security name, so the
ticker needed for price lookups is resolved from the ISIN on creation.
When that fails (the source only covers UCITS ETFs, so ETCs and single
stocks come back empty) the instrument is still created — automatic
pricing simply stays off until the user fills the ticker in.
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.config import get_settings
from app.models.instrument import Instrument
from app.models.transaction import Transaction
from app.providers.registry import resolve_ticker
from app.services.fineco_import import parse_fineco_xlsx


def import_fineco_xlsx(session: Session, data: bytes) -> dict:
    settings = get_settings()
    parsed = parse_fineco_xlsx(data)

    instruments = session.exec(select(Instrument)).all()
    instrument_by_isin = {i.isin: i for i in instruments if i.isin}
    used_tickers = {i.ticker for i in instruments if i.ticker}

    existing_keys = set(session.exec(select(Transaction.dedup_key)).all())

    imported = 0
    duplicates = 0
    created_instruments: list[str] = []

    for p in parsed:
        instrument = instrument_by_isin.get(p.isin)
        if instrument is None:
            # Not in the export — look it up so the user doesn't have to.
            ticker = resolve_ticker(p.isin, settings.default_composition_provider)
            if ticker and ticker in used_tickers:
                # Two ISINs resolving to the same symbol would violate the
                # unique constraint; leave the later one manual.
                ticker = None
            instrument = Instrument(
                isin=p.isin,
                ticker=ticker,
                name=p.name,
                currency=p.currency,
                # Without a ticker a price fetch would only fail noisily.
                auto_price_enabled=bool(ticker),
                included=True,
            )
            if ticker:
                used_tickers.add(ticker)
            session.add(instrument)
            session.commit()
            session.refresh(instrument)
            instrument_by_isin[p.isin] = instrument
            created_instruments.append(p.name)

        if p.dedup_key in existing_keys:
            duplicates += 1
            continue

        session.add(
            Transaction(
                instrument_id=instrument.id,
                isin=p.isin,
                name=p.name,
                trade_date=p.trade_date,
                value_date=p.value_date,
                sign=p.sign,
                quantity=p.quantity,
                currency=p.currency,
                price=p.price,
                fx_rate=p.fx_rate,
                gross_amount=p.gross_amount,
                commissions=p.commissions,
                dedup_key=p.dedup_key,
            )
        )
        existing_keys.add(p.dedup_key)
        imported += 1

    session.commit()

    return {
        "imported": imported,
        "duplicates": duplicates,
        "created_instruments": created_instruments,
    }


def list_transactions(session: Session) -> list[Transaction]:
    return session.exec(
        select(Transaction).order_by(Transaction.trade_date.desc())
    ).all()


def transactions_by_instrument(session: Session) -> dict[int, list[Transaction]]:
    grouped: dict[int, list[Transaction]] = defaultdict(list)
    for t in session.exec(select(Transaction).order_by(Transaction.trade_date)).all():
        grouped[t.instrument_id].append(t)
    return grouped
