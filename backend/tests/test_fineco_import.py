"""Parser + import-service coverage using a synthetic in-memory xlsx
mirroring the Fineco 'Movimenti Dossier Titoli' layout."""

from io import BytesIO

import openpyxl
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models.instrument import Instrument
from app.models.transaction import Transaction, TransactionSign
from app.services.fineco_import import parse_fineco_xlsx
from app.services.transactions_service import import_fineco_xlsx


def _make_xlsx(rows: list[tuple]) -> bytes:
    """rows are the operation rows; header/metadata are prepended to
    match the real export shape."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("Dossier n.: 123", None))
    ws.append((None,))
    ws.append(("RISULTATO RICERCA MOVIMENTI TITOLI", None))
    ws.append((None,))
    ws.append((
        "Operazione", "Data valuta", "Descrizione", "Titolo", "Isin", "Segno",
        "Quantita", "Divisa", "Prezzo", "Cambio", "Controvalore",
        "Commissioni Fondi Sw/Ingr/Uscita", "Commissioni amministrato",
    ))
    ws.append((None,))
    for r in rows:
        ws.append(r)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _row(op, isin, name, qty, price, ctv, comm=None):
    return (op, "14/07/2026", "Compravendita titoli", name, isin, "A", qty, "EUR", price, 1, ctv, comm, None)


def test_parse_extracts_fields_and_commissions():
    data = _make_xlsx([
        _row("10/07/2026", "IE00BKM4GZ66", "ISHS MSCI EM", 7, 47.78, 334.46, 2.95),
    ])
    parsed = parse_fineco_xlsx(data)
    assert len(parsed) == 1
    t = parsed[0]
    assert t.isin == "IE00BKM4GZ66"
    assert t.sign == TransactionSign.buy
    assert t.quantity == 7
    assert t.price == 47.78
    assert t.gross_amount == 334.46
    assert t.commissions == 2.95
    assert t.trade_date.isoformat() == "2026-07-10"


def _client_with_fresh_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    return TestClient(app), engine


def test_import_links_held_only_and_is_idempotent():
    client, engine = _client_with_fresh_db()
    try:
        with Session(engine) as s:
            s.add(Instrument(isin="IE00BKM4GZ66", ticker="EIMI.MI", name="Emerging", currency="EUR"))
            s.commit()

        data = _make_xlsx([
            _row("10/07/2026", "IE00BKM4GZ66", "ISHS MSCI EM", 7, 47.78, 334.46),
            _row("10/07/2026", "IE00B8XB7377", "FINEX GOLD", 11, 2.7, 30.09),  # not held
        ])

        resp = client.post("/api/transactions/import", files={"file": ("f.xlsx", data)})
        assert resp.status_code == 200
        body = resp.json()
        assert body["imported"] == 1
        assert len(body["skipped"]) == 1
        assert body["skipped"][0]["isin"] == "IE00B8XB7377"

        # Re-import: idempotent.
        resp2 = client.post("/api/transactions/import", files={"file": ("f.xlsx", data)})
        assert resp2.json()["imported"] == 0
        assert resp2.json()["duplicates"] == 1

        with Session(engine) as s:
            assert len(s.exec(select(Transaction)).all()) == 1
    finally:
        app.dependency_overrides.clear()


def test_import_rejects_non_fineco_file():
    client, _ = _client_with_fresh_db()
    try:
        wb = openpyxl.Workbook()
        wb.active.append(("just", "some", "columns"))
        buf = BytesIO()
        wb.save(buf)
        resp = client.post("/api/transactions/import", files={"file": ("x.xlsx", buf.getvalue())})
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()
