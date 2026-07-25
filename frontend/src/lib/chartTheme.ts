/** Shared chart styling.
 *
 * Every chart previously hardcoded its own colours and left the axes at
 * Recharts' defaults, so they looked like three different libraries on
 * one page. These constants mirror the CSS tokens (Recharts needs real
 * values, not `var(--x)`) and are read from the document at runtime so
 * light and dark mode both work.
 */

function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export const chart = {
  get axis() {
    return cssVar("--text-faint", "#6b7385");
  },
  get grid() {
    return cssVar("--border", "#262b36");
  },
  get accent() {
    return cssVar("--accent", "#a06bff");
  },
  get pos() {
    return cssVar("--pos", "#3ddc97");
  },
  get muted() {
    return cssVar("--text-muted", "#9aa3b2");
  },
};

/** Categorical palette. Ordered so the first few stay distinguishable
 * for viewers with common colour-vision deficiencies (hue *and*
 * lightness vary between neighbours, not hue alone). */
export const SERIES_COLORS = [
  "#a06bff",
  "#3bc9ff",
  "#f0b429",
  "#3ddc97",
  "#ff6b81",
  "#8f6bff",
  "#3bffd5",
  "#ff8f3b",
  "#6e9bff",
  "#c0ff3b",
  "#ff3bd5",
  "#3b8fff",
];

/** Axis props shared by every chart: no axis line, no tick marks, muted
 * 11px labels. Chart junk removed so the data carries the ink. */
export const axisProps = {
  stroke: "transparent",
  tick: { fill: chart.axis, fontSize: 11 },
  tickLine: false,
  axisLine: false,
} as const;

export const gridProps = {
  stroke: chart.grid,
  strokeDasharray: "2 4",
  vertical: false,
} as const;

/** Recharts' entrance animation never completes in this environment and
 * leaves charts blank, so every series opts out. */
export const noAnimation = { isAnimationActive: false } as const;
