"""Persistence + linking for imported transactions.

Seam between the pure Fineco parser and the DB. The export is the source
of truth for the portfolio: every ISIN it mentions becomes an Instrument
(created on first sight), and positions are derived from these rows —
nothing is entered by hand. The user then chooses which instruments to
count via `Instrument.included`.

New instruments arrive without a ticker (the export carries only ISIN
and the broker's security name), so automatic pricing stays off until
the user supplies one.
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.models.instrument import Instrument
from app.models.transaction import Transaction
from app.services.fineco_import import parse_fineco_xlsx


def import_fineco_xlsx(session: Session, data: bytes) -> dict:
    parsed = parse_fineco_xlsx(data)

    instruments = session.exec(select(Instrument)).all()
    instrument_by_isin = {i.isin: i for i in instruments if i.isin}

    existing_keys = set(session.exec(select(Transaction.dedup_key)).all())

    imported = 0
    duplicates = 0
    created_instruments: list[str] = []

    for p in parsed:
        instrument = instrument_by_isin.get(p.isin)
        if instrument is None:
            instrument = Instrument(
                isin=p.isin,
                ticker=None,  # not in the export; user adds it for pricing
                name=p.name,
                currency=p.currency,
                # No ticker yet, so a price fetch would only fail noisily.
                auto_price_enabled=False,
                included=True,
            )
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
