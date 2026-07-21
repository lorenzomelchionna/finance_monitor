/** Client-side time-series transforms for the history charts. The
 * backend returns the full available daily series once; horizon slicing
 * and smoothing happen here so switching views hits no network. */

export interface TsPoint {
  date: string; // ISO YYYY-MM-DD
  value: number;
}

export type Horizon = "1M" | "3M" | "6M" | "1A" | "3A" | "5A" | "MAX";

export const HORIZONS: Horizon[] = ["1M", "3M", "6M", "1A", "3A", "5A", "MAX"];

const HORIZON_DAYS: Record<Horizon, number | null> = {
  "1M": 30,
  "3M": 90,
  "6M": 180,
  "1A": 365,
  "3A": 365 * 3,
  "5A": 365 * 5,
  MAX: null,
};

/** Keep only points within `horizon` of the series' last date. Cutoff is
 * measured from the data's own end (not today) so a stale series still
 * shows a full window. Assumes `points` is sorted ascending by date. */
export function sliceByHorizon(points: TsPoint[], horizon: Horizon): TsPoint[] {
  const days = HORIZON_DAYS[horizon];
  if (days === null || points.length === 0) return points;

  const lastMs = new Date(points[points.length - 1].date).getTime();
  const cutoffMs = lastMs - days * 24 * 60 * 60 * 1000;
  return points.filter((p) => new Date(p.date).getTime() >= cutoffMs);
}

/** Trailing simple moving average over `window` points. window <= 1
 * returns the input unchanged. Each output keeps the original date and
 * averages up to `window` preceding values (fewer at the start). */
export function movingAverage(points: TsPoint[], window: number): TsPoint[] {
  if (window <= 1 || points.length === 0) return points;

  const out: TsPoint[] = [];
  let sum = 0;
  const q: number[] = [];
  for (const p of points) {
    q.push(p.value);
    sum += p.value;
    if (q.length > window) sum -= q.shift()!;
    out.push({ date: p.date, value: sum / q.length });
  }
  return out;
}
