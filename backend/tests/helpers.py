from app.providers.base import InstrumentRef, PriceQuote


class FakeAutoProvider:
    """Stand-in for YFinanceProvider so tests never hit the network."""

    def __init__(self, quote: PriceQuote | None) -> None:
        self._quote = quote

    def get_price(self, ref: InstrumentRef) -> PriceQuote | None:
        return self._quote
