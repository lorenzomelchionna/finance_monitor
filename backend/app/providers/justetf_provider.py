"""JustETF-backed CompositionProvider: scrapes the public ETF profile
page for an ISIN and extracts the top geographic + sector weights.

Fragile by nature (it parses a public HTML page, not an official API):
the page layout can change and the source can rate-limit/block. Every
failure returns None so the caller degrades to the manual fallback. The
extraction keys off stable `data-testid` attributes rather than visual
structure, which is the most robust hook the page offers.

The page exposes the top-4 buckets per dimension plus an aggregated
"Other" — enough for portfolio-level exposure; the long tail is folded
into "Other".
"""

import logging
import re
import urllib.error
import urllib.request

from app.providers.base import BreakdownWeight, InstrumentRef

logger = logging.getLogger(__name__)

_URL = "https://www.justetf.com/en/etf-profile.html?isin={isin}"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# dimension name (our vocabulary) -> JustETF testid infix
_DIMENSIONS = {"geography": "countries", "sector": "sectors"}


def _fetch(isin: str) -> str | None:
    req = urllib.request.Request(_URL.format(isin=isin), headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.warning("JustETF fetch failed for %s", isin, exc_info=True)
        return None


def _parse_dimension(html: str, infix: str) -> list[BreakdownWeight]:
    names = re.findall(rf'tl_etf-holdings_{infix}_value_name">([^<]+)</td>', html)
    pcts = re.findall(rf'tl_etf-holdings_{infix}_value_percentage">([0-9.,]+)%', html)
    out: list[BreakdownWeight] = []
    for name, pct in zip(names, pcts):
        try:
            weight = float(pct.replace(",", ".")) / 100.0
        except ValueError:
            continue
        out.append(BreakdownWeight(key=name.strip(), weight=weight))
    return out


class JustEtfCompositionProvider:
    def get_breakdowns(self, ref: InstrumentRef) -> dict[str, list[BreakdownWeight]] | None:
        if not ref.isin:
            return None
        html = _fetch(ref.isin)
        if html is None:
            return None

        result: dict[str, list[BreakdownWeight]] = {}
        for dimension, infix in _DIMENSIONS.items():
            weights = _parse_dimension(html, infix)
            # Skip a dimension the page can't break down (e.g. a single
            # "Other" = 100% for a govt-bond ETF's sectors).
            meaningful = [w for w in weights if w.key.lower() != "other"]
            if meaningful:
                result[dimension] = weights
        return result or None
