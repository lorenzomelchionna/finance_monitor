import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TsPoint } from "../lib/timeseries";

export interface BuyMarker {
  date: string; // snapped to a series date
  value: number; // y position on the chart
  quantity: number;
  price: number;
}

interface Props {
  points: TsPoint[];
  markers?: BuyMarker[];
  /** Unit label for tooltip, e.g. "EUR". */
  unit?: string;
  color?: string;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getFullYear()).slice(2)}`;
}

/** Single-series daily line chart with optional buy markers. Markers are
 * merged into the same data array (keyed by date) and drawn as a Scatter
 * so they share the category X axis with the line.
 *
 * isAnimationActive is off — Recharts' entrance animation never
 * completes in this environment and leaves the chart blank (same gotcha
 * as FanChart / CurrencyExposurePie). */
export function HistoryChart({ points, markers = [], unit, color = "#3bc9ff" }: Props) {
  if (points.length === 0) {
    return <p className="placeholder">Nessun dato per l'orizzonte selezionato.</p>;
  }

  const markerByDate = new Map(markers.map((m) => [m.date, m]));
  const data = points.map((p) => {
    const m = markerByDate.get(p.date);
    return { date: p.date, value: p.value, buy: m ? m.value : undefined, marker: m };
  });

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
        <XAxis dataKey="date" tickFormatter={formatDate} minTickGap={48} />
        <YAxis
          tickFormatter={(v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          width={72}
          domain={["auto", "auto"]}
        />
        <Tooltip
          labelFormatter={(d) => new Date(String(d)).toLocaleDateString("it-IT")}
          formatter={(value, name, entry) => {
            if (name === "Acquisto") {
              const m = entry?.payload?.marker as BuyMarker | undefined;
              if (m) {
                return [`${m.quantity} @ ${m.price.toLocaleString("it-IT")} ${unit ?? ""}`.trim(), "Acquisto"];
              }
            }
            return [
              `${Number(value).toLocaleString("it-IT", { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ""}`,
              "Valore",
            ];
          }}
        />
        <Line
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
          name="Valore"
        />
        <Scatter
          dataKey="buy"
          fill="#ff5c8a"
          isAnimationActive={false}
          name="Acquisto"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
