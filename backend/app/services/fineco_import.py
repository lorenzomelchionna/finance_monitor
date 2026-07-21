"""Parser for the Fineco "Movimenti Dossier Titoli" xlsx export.

Pure parsing (bytes -> list of ParsedTransaction); no DB access. The
persistence/linking step lives in transactions_service so this can be
unit-tested on a raw file without a database.

The export has a few metadata rows, then a header row containing
'Isin', then one row per operation. Columns are located by header name
(not fixed index) so a future column reorder doesn't break parsing.
"""

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO

import openpyxl

from app.models.transaction import TransactionSign


@dataclass(frozen=True)
class ParsedTransaction:
    isin: str
    name: str
    trade_date: date
    value_date: date | None
    sign: TransactionSign
    quantity: float
    currency: str
    price: float
    fx_rate: float
    gross_amount: float
    commissions: float

    @property
    def dedup_key(self) -> str:
        raw = f"{self.isin}|{self.trade_date.isoformat()}|{self.sign.value}|{self.quantity}|{self.price}|{self.gross_amount}"
        return hashlib.sha1(raw.encode()).hexdigest()


# Header label -> canonical field. Matched case-insensitively on a
# stripped prefix so slight label variations still resolve.
_HEADER_ALIASES = {
    "operazione": "trade_date",
    "data valuta": "value_date",
    "descrizione": "description",
    "titolo": "name",
    "isin": "isin",
    "segno": "sign",
    "quantita": "quantity",
    "divisa": "currency",
    "prezzo": "price",
    "cambio": "fx_rate",
    "controvalore": "gross_amount",
}


def _norm(label: object) -> str:
    return str(label).strip().lower() if label is not None else ""


def _to_date(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    # Fineco exports dates as dd/mm/yyyy strings.
    return datetime.strptime(str(value).strip(), "%d/%m/%Y").date()


def _to_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Tolerate it-IT decimal comma just in case.
    return float(str(value).strip().replace(",", "."))


def parse_fineco_xlsx(data: bytes) -> list[ParsedTransaction]:
    wb = openpyxl.load_workbook(BytesIO(data), data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))

    # Locate the header row (the one containing an 'isin' cell).
    header_idx = None
    for i, row in enumerate(rows):
        if any(_norm(c) == "isin" for c in row):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Header row with 'Isin' not found — not a Fineco movements export?")

    header = rows[header_idx]
    col_of: dict[str, int] = {}
    commission_cols: list[int] = []
    for idx, label in enumerate(header):
        n = _norm(label)
        if n in _HEADER_ALIASES:
            col_of[_HEADER_ALIASES[n]] = idx
        elif n.startswith("commissioni") or n.startswith("spese"):
            commission_cols.append(idx)

    required = {"trade_date", "isin", "sign", "quantity", "price", "gross_amount"}
    missing = required - col_of.keys()
    if missing:
        raise ValueError(f"Missing expected columns in export: {sorted(missing)}")

    def cell(row, field):
        i = col_of.get(field)
        return row[i] if i is not None and i < len(row) else None

    parsed: list[ParsedTransaction] = []
    for row in rows[header_idx + 1:]:
        isin = cell(row, "isin")
        if not isin or str(isin).strip() == "":
            continue  # blank/separator row

        sign_raw = _norm(cell(row, "sign")).upper()
        try:
            sign = TransactionSign(sign_raw.upper())
        except ValueError:
            # Unknown sign — skip rather than guess.
            continue

        commissions = sum(_to_float(row[i]) for i in commission_cols if i < len(row))

        parsed.append(
            ParsedTransaction(
                isin=str(isin).strip(),
                name=str(cell(row, "name") or "").strip(),
                trade_date=_to_date(cell(row, "trade_date")),
                value_date=_to_date(cell(row, "value_date")),
                sign=sign,
                quantity=_to_float(cell(row, "quantity")),
                currency=str(cell(row, "currency") or "EUR").strip(),
                price=_to_float(cell(row, "price")),
                fx_rate=_to_float(cell(row, "fx_rate")) or 1.0,
                gross_amount=_to_float(cell(row, "gross_amount")),
                commissions=commissions,
            )
        )
    return parsed
