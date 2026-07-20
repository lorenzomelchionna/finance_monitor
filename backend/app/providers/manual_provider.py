"""DB-backed fallback price provider.

Reads the most recent manually-entered PriceSnapshot for an instrument.
Always available (no network call) — this is what the registry degrades
to when the auto provider has no coverage or is disabled per-instrument.
"""

from sqlmodel import Session, select

from app.models.price import PriceSnapshot, PriceSource
from app.providers.base import InstrumentRef, PriceQuote


class ManualPriceProvider:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_price(self, ref: InstrumentRef) -> PriceQuote | None:
        statement = (
            select(PriceSnapshot)
            .where(
                PriceSnapshot.instrument_id == ref.id,
                PriceSnapshot.source == PriceSource.manual,
            )
            .order_by(PriceSnapshot.as_of.desc())
        )
        snapshot = self._session.exec(statement).first()
        if snapshot is None:
            return None
        return PriceQuote(price=snapshot.price, currency=snapshot.currency, as_of=snapshot.as_of)
