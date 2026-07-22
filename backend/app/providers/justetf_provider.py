"""JustETF-backed CompositionProvider: scrapes the public ETF profile
page for an ISIN and extracts the full geographic + sector weights.

Fragile by nature (it parses a public HTML page, not an official API):
the layout can change and the source can rate-limit/block. Every failure
returns None so the caller degrades to the manual fallback. Extraction
keys off stable `data-testid` attributes, the most robust hook available.

The profile page renders only the top-4 buckets per dimension plus an
aggregated "Other". To keep "Other" as small as possible we drive the
page's own "show more" control: a fresh session starts collapsed, and
one Wicket-Ajax call per dimension expands it to the full list. The
expand endpoint is a stateful toggle, so a *fresh* cookie jar is used
per fetch. If the expand call fails we fall back to the collapsed
top-4 already in the page.
"""

import html as html_lib
import http.cookiejar
import logging
import re
import urllib.error
import urllib.request

from app.providers.base import BreakdownWeight, InstrumentRef

logger = logging.getLogger(__name__)

_PROFILE_URL = "https://www.justetf.com/en/etf-profile.html?isin={isin}"
_BASE = "https://www.justetf.com"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# dimension name (our vocabulary) -> (JustETF testid infix, expand-link testid)
_DIMENSIONS = {
    "geography": ("countries", "loadMoreCountries"),
    "sector": ("sectors", "loadMoreSectors"),
}


def _opener() -> urllib.request.OpenerDirector:
    # Fresh cookie jar per fetch: the expand link is a toggle whose state
    # lives in the session, so reusing a jar would collapse it again.
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _get(opener, url: str, ajax_isin: str | None = None) -> str | None:
    headers = {"User-Agent": _UA}
    if ajax_isin is not None:
        headers["Wicket-Ajax"] = "true"
        headers["Wicket-Ajax-BaseURL"] = f"en/etf-profile.html?isin={ajax_isin}"
        headers["X-Requested-With"] = "XMLHttpRequest"
    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.warning("JustETF request failed: %s", url, exc_info=True)
        return None


def _parse_dimension(text: str, infix: str) -> list[BreakdownWeight]:
    names = re.findall(rf'tl_etf-holdings_{infix}_value_name">([^<]+)</td>', text)
    pcts = re.findall(rf'tl_etf-holdings_{infix}_value_percentage">([0-9.,]+)%', text)
    out: list[BreakdownWeight] = []
    for name, pct in zip(names, pcts):
        try:
            weight = float(pct.replace(",", ".")) / 100.0
        except ValueError:
            continue
        out.append(BreakdownWeight(key=name.strip(), weight=weight))
    return out


def _expand_href(page_html: str, expand_testid: str) -> str | None:
    """The full 'show more' link (with its Wicket component version) is
    embedded in a Wicket-Ajax config blob as `"u":"<url>"` — extract it so
    we don't hardcode a render version that may change."""
    m = re.search(rf'"u":"([^"]*{expand_testid}[^"]*)"', page_html)
    if not m:
        return None
    return html_lib.unescape(m.group(1))


class JustEtfCompositionProvider:
    def get_breakdowns(self, ref: InstrumentRef) -> dict[str, list[BreakdownWeight]] | None:
        if not ref.isin:
            return None
        opener = _opener()
        page = _get(opener, _PROFILE_URL.format(isin=ref.isin))
        if page is None:
            return None

        result: dict[str, list[BreakdownWeight]] = {}
        for dimension, (infix, expand_testid) in _DIMENSIONS.items():
            # Prefer the expanded full list; fall back to the collapsed
            # top-4 already in the page.
            weights = self._expanded_or_collapsed(opener, page, ref.isin, infix, expand_testid)
            meaningful = [w for w in weights if w.key.lower() != "other"]
            if meaningful:
                result[dimension] = weights
        return result or None

    def _expanded_or_collapsed(
        self, opener, page: str, isin: str, infix: str, expand_testid: str
    ) -> list[BreakdownWeight]:
        href = _expand_href(page, expand_testid)
        if href:
            ajax = _get(opener, _BASE + href, ajax_isin=isin)
            if ajax:
                expanded = _parse_dimension(ajax, infix)
                if expanded:
                    return expanded
        return _parse_dimension(page, infix)
