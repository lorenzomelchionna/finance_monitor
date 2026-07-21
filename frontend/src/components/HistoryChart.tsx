import {
  CartesianGrid,
  ComposedChart,
  Legend,
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
  /** Optional cumulative-invested overlay (step line), aligned by date.
   * Used on the portfolio-aggregate view for "invested vs value". */
  investedPoints?: TsPoint[];
  /** Unit label for tooltip, e.g. "EUR". */
  unit?: string;
  color?: string;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getFullYear()).slice(2)}`;
}

const fmt = (v: number, unit?: string) =>
  `${v.toLocaleString("it-IT", { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ""}`;

interface ChartTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: { payload?: { marker?: BuyMarker; value?: number; invested?: number } }[];
  unit?: string;
}

/** Custom tooltip: renders only the series that actually have a value at
 * the hovered date. Without this the Scatter ("Acquisto") shows up on
 * every point as "NaN" because its dataKey is undefined off-marker. */
function ChartTooltip({ active, payload, label, unit }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const row = payload[0]?.payload;
  const lines: { key: string; color: string; text: string }[] = [];

  if (row?.value != null && Number.isFinite(row.value)) {
    lines.push({ key: "value", color: "#3bc9ff", text: `Valore: ${fmt(row.value, unit)}` });
  }
  if (row?.invested != null && Number.isFinite(row.invested)) {
    lines.push({ key: "invested", color: "#9aa0aa", text: `Investito: ${fmt(row.invested, unit)}` });
  }
  if (row?.marker) {
    lines.push({
      key: "buy",
      color: "#ff5c8a",
      text: `Acquisto: ${row.marker.quantity} @ ${fmt(row.marker.price, unit)}`,
    });
  }
  if (lines.length === 0) return null;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{new Date(String(label)).toLocaleDateString("it-IT")}</div>
      {lines.map((l) => (
        <div key={l.key} style={{ color: l.color }}>
          {l.text}
        </div>
      ))}
    </div>
  );
}

/** Single-series daily line chart with optional buy markers. Markers are
 * merged into the same data array (keyed by date) and drawn as a Scatter
 * so they share the category X axis with the line.
 *
 * isAnimationActive is off — Recharts' entrance animation never
 * completes in this environment and leaves the chart blank (same gotcha
 * as FanChart / CurrencyExposurePie). */
export function HistoryChart({
  points,
  markers = [],
  investedPoints,
  unit,
  color = "#3bc9ff",
}: Props) {
  if (points.length === 0) {
    return <p className="placeholder">Nessun dato per l'orizzonte selezionato.</p>;
  }

  const markerByDate = new Map(markers.map((m) => [m.date, m]));
  const investedByDate = new Map((investedPoints ?? []).map((p) => [p.date, p.value]));
  const data = points.map((p) => {
    const m = markerByDate.get(p.date);
    return {
      date: p.date,
      value: p.value,
      buy: m ? m.value : undefined,
      marker: m,
      invested: investedByDate.get(p.date),
    };
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
        <Tooltip content={<ChartTooltip unit={unit} />} />
        <Legend />
        {investedPoints && investedPoints.length > 0 && (
          <Line
            dataKey="invested"
            stroke="#9aa0aa"
            strokeWidth={1.5}
            strokeDasharray="5 4"
            dot={false}
            type="stepAfter"
            isAnimationActive={false}
            name="Investito"
            connectNulls
          />
        )}
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
