/** Parse a number typed with either a dot or a comma as decimal
 * separator. Browsers on it-IT locale accept "139,77" into a native
 * <input type="number">, but `Number()` treats the comma as invalid
 * and returns NaN — this normalizes before parsing. */
export function parseLocaleNumber(value: string): number {
  return Number(value.replace(",", "."));
}
