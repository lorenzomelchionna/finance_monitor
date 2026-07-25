/** Single source of truth for how numbers are shown.
 *
 * The app is Italian and money-centric, so figures were being rendered
 * with `toFixed()` — dot decimals, no thousands separator, no currency —
 * which read as raw JSON rather than as money, and clashed with the few
 * places that did use it-IT. Everything goes through here now.
 */

const LOCALE = "it-IT";

/** Money with a currency symbol: "6.595,51 €". */
export function money(value: number, currency = "EUR", digits = 2): string {
  return value.toLocaleString(LOCALE, {
    style: "currency",
    currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** Money without the symbol — for table columns whose header already
 * states the currency, where repeating it on every row is noise. */
export function amount(value: number, digits = 2): string {
  return value.toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** Signed money, so gains and losses are distinguishable at a glance
 * even before colour: "+653,09 €" / "−16,80 €". */
export function signedMoney(value: number, currency = "EUR"): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${money(Math.abs(value), currency)}`;
}

/** A 0..1 fraction as a signed percentage: "+17,3%". */
export function signedPercent(fraction: number, digits = 1): string {
  const pct = fraction * 100;
  const sign = pct > 0 ? "+" : pct < 0 ? "−" : "";
  return `${sign}${Math.abs(pct).toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

/** A 0..1 fraction as a plain percentage: "38,2%". */
export function percent(fraction: number, digits = 1): string {
  return `${(fraction * 100).toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

/** Quantities: no forced decimals — "27", "187", "12,5". */
export function quantity(value: number): string {
  return value.toLocaleString(LOCALE, { maximumFractionDigits: 4 });
}

export function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(LOCALE, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Axis ticks: "6,6k" keeps a dense time axis readable. */
export function compact(value: number): string {
  return value.toLocaleString(LOCALE, {
    notation: "compact",
    maximumFractionDigits: 1,
  });
}

/** Sign class for colouring a figure, or "" when flat/unknown. */
export function toneOf(value: number | null | undefined): string {
  if (value == null) return "";
  return value > 0 ? "pos" : value < 0 ? "neg" : "";
}
