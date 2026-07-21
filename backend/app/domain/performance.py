"""Pure performance math derived from the transaction ledger:
transaction-based cost basis, money-weighted return (XIRR) and the
cumulative-invested series for the "invested vs value" overlay.

No DB / no I/O — inputs are plain tuples/dataclasses assembled by the
caller, so every function here is unit-testable in isolation.

Sign convention for XIRR cashflows: money leaving the pocket (a buy) is
negative; money coming back (a sell, or the current market value taken
as a final synthetic inflow) is positive.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TxnLike:
    """The subset of a Transaction the performance math needs."""

    instrument_id: int
    trade_date: date
    sign: str  # "A" (buy) | "V" (sell)
    quantity: float
    price: float
    gross_amount: float
    commissions: float


@dataclass(frozen=True)
class CostBasis:
    quantity: float  # net quantity still held per the ledger
    invested: float  # net cash put in (base currency), commissions included
    avg_cost: float  # invested / quantity (0 if flat)
    commissions: float  # total commissions paid


def cost_basis_by_instrument(txns: list[TxnLike]) -> dict[int, CostBasis]:
    """Running average-cost basis per instrument. On a sell, invested is
    reduced proportionally at the current average cost (realized P/L is
    out of scope here — all current data is buys)."""
    acc: dict[int, dict] = {}
    for t in sorted(txns, key=lambda x: x.trade_date):
        a = acc.setdefault(t.instrument_id, {"qty": 0.0, "invested": 0.0, "comm": 0.0})
        if t.sign == "A":
            a["invested"] += t.gross_amount + t.commissions
            a["qty"] += t.quantity
            a["comm"] += t.commissions
        elif t.sign == "V":
            avg = a["invested"] / a["qty"] if a["qty"] > 0 else 0.0
            a["invested"] -= avg * t.quantity
            a["qty"] -= t.quantity
            a["comm"] += t.commissions

    result: dict[int, CostBasis] = {}
    for iid, a in acc.items():
        qty = a["qty"]
        result[iid] = CostBasis(
            quantity=qty,
            invested=a["invested"],
            avg_cost=(a["invested"] / qty) if qty > 0 else 0.0,
            commissions=a["comm"],
        )
    return result


def _xnpv(rate: float, flows: list[tuple[date, float]], t0: date) -> float:
    return sum(amt / (1.0 + rate) ** ((d - t0).days / 365.0) for d, amt in flows)


def xirr(flows: list[tuple[date, float]]) -> float | None:
    """Annualized money-weighted return for dated cashflows. Returns None
    when there aren't both an inflow and an outflow, or no root can be
    bracketed. Uses bisection (robust) over a wide rate band."""
    if len(flows) < 2:
        return None
    has_neg = any(a < 0 for _, a in flows)
    has_pos = any(a > 0 for _, a in flows)
    if not (has_neg and has_pos):
        return None

    t0 = min(d for d, _ in flows)

    low, high = -0.9999, 10.0
    f_low = _xnpv(low, flows, t0)
    f_high = _xnpv(high, flows, t0)

    # Expand the upper bound if the root isn't bracketed yet.
    expand = 0
    while f_low * f_high > 0 and expand < 40:
        high *= 1.5
        f_high = _xnpv(high, flows, t0)
        expand += 1
    if f_low * f_high > 0:
        return None

    for _ in range(200):
        mid = (low + high) / 2.0
        f_mid = _xnpv(mid, flows, t0)
        if abs(f_mid) < 1e-8:
            return mid
        if f_low * f_mid < 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2.0


def cumulative_invested(txns: list[TxnLike], dates: list[str]) -> list[float]:
    """Net cash invested (buys gross+commissions minus sell proceeds) as
    of each ISO date in `dates` (assumed ascending). Step series for the
    'invested vs value' overlay."""
    events = sorted(
        (
            (t.trade_date.isoformat(), (t.gross_amount + t.commissions) if t.sign == "A" else -t.gross_amount)
            for t in txns
        ),
        key=lambda x: x[0],
    )
    out: list[float] = []
    running = 0.0
    i = 0
    for d in dates:
        while i < len(events) and events[i][0] <= d:
            running += events[i][1]
            i += 1
        out.append(running)
    return out
