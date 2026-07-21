"""Persistence + linking for imported transactions.

Seam between the pure Fineco parser and the DB. Only operations whose
ISIN matches an instrument already in the portfolio are stored (per
"solo per quelli presenti in portafoglio"); everything else is reported
back as skipped so the UI can surface it.
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
    skipped_not_in_portfolio: dict[str, str] = {}  # isin -> name

    for p in parsed:
        instrument = instrument_by_isin.get(p.isin)
        if instrument is None:
            skipped_not_in_portfolio[p.isin] = p.name
            continue
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
        "skipped": [
            {"isin": isin, "name": name} for isin, name in skipped_not_in_portfolio.items()
        ],
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
