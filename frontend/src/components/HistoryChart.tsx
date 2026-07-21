import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TsPoint } from "../lib/timeseries";

interface Props {
  points: TsPoint[];
  /** Unit label for tooltip/axis, e.g. "EUR". */
  unit?: string;
  color?: string;
}

function formatDate(iso: string): string {
  // Compact it-IT style: "mar 21" style is overkill; use MM/YY for axis.
  const d = new Date(iso);
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getFullYear()).slice(2)}`;
}

/** Single-series daily line chart. isAnimationActive is off — Recharts'
 * entrance animation never completes in this environment and leaves the
 * chart blank (same gotcha as FanChart / CurrencyExposurePie). */
export function HistoryChart({ points, unit, color = "#3bc9ff" }: Props) {
  if (points.length === 0) {
    return <p className="placeholder">Nessun dato per l'orizzonte selezionato.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart data={points} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          minTickGap={48}
        />
        <YAxis
          tickFormatter={(v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          width={72}
          domain={["auto", "auto"]}
        />
        <Tooltip
          labelFormatter={(d) => new Date(String(d)).toLocaleDateString("it-IT")}
          formatter={(value) => [
            `${Number(value).toLocaleString("it-IT", { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ""}`,
            "Valore",
          ]}
        />
        <Line
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
