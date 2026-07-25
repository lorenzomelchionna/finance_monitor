import {
  Area,
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
import { axisProps, chart, gridProps, noAnimation } from "../lib/chartTheme";
import { amount, compact, money, shortDate } from "../lib/format";
import type { TsPoint } from "../lib/timeseries";

export interface BuyMarker {
  date: string;
  value: number;
  quantity: number;
  price: number;
}

interface Props {
  points: TsPoint[];
  markers?: BuyMarker[];
  /** Cumulative-invested step line, for the portfolio view. */
  investedPoints?: TsPoint[];
  unit?: string;
  color?: string;
}

/** Month/year tick. The axis previously formatted every point and let
 * Recharts thin them out, which produced duplicate labels ("06/26"
 * twice) whenever two kept ticks fell in the same month. Ticks are now
 * chosen explicitly: one per month boundary, thinned to fit. */
function monthLabel(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getFullYear()).slice(2)}`;
}

function pickTicks(points: TsPoint[], max = 8): string[] {
  if (points.length === 0) return [];
  // First date of each distinct month present in the series.
  const firstOfMonth: string[] = [];
  let seen = "";
  for (const p of points) {
    const key = p.date.slice(0, 7);
    if (key !== seen) {
      seen = key;
      firstOfMonth.push(p.date);
    }
  }
  if (firstOfMonth.length <= max) return firstOfMonth;
  const step = Math.ceil(firstOfMonth.length / max);
  return firstOfMonth.filter((_, i) => i % step === 0);
}

interface ChartTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: { payload?: { marker?: BuyMarker; value?: number; invested?: number } }[];
  unit?: string;
}

/** Renders only series with a value at the hovered date. Without this
 * the Scatter shows up on every point as "NaN", since its dataKey is
 * undefined off-marker. */
function ChartTooltip({ active, payload, label, unit }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  const fmt = (v: number) => (unit ? money(v, unit) : amount(v));

  const lines: { key: string; color: string; text: string }[] = [];
  if (row?.value != null && Number.isFinite(row.value)) {
    lines.push({ key: "value", color: chart.accent, text: `Valore ${fmt(row.value)}` });
  }
  if (row?.invested != null && Number.isFinite(row.invested)) {
    lines.push({ key: "invested", color: chart.muted, text: `Investito ${fmt(row.invested)}` });
  }
  if (row?.marker) {
    lines.push({
      key: "buy",
      color: "#ff6b81",
      text: `Acquisto ${row.marker.quantity} @ ${fmt(row.marker.price)}`,
    });
  }
  if (!lines.length) return null;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{shortDate(String(label))}</div>
      {lines.map((l) => (
        <div key={l.key} style={{ color: l.color }}>
          {l.text}
        </div>
      ))}
    </div>
  );
}

export function HistoryChart({ points, markers = [], investedPoints, unit, color }: Props) {
  if (points.length === 0) {
    return <p className="placeholder">Nessun dato per l'orizzonte selezionato.</p>;
  }

  const lineColor = color ?? chart.accent;
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

  const hasInvested = (investedPoints?.length ?? 0) > 0;

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <defs>
          {/* A soft fill under the line gives the series visual weight
              without the heavier ink of a solid area. */}
          <linearGradient id="valueFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity={0.22} />
            <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
          </linearGradient>
        </defs>

        <CartesianGrid {...gridProps} />
        <XAxis
          dataKey="date"
          ticks={pickTicks(points)}
          tickFormatter={monthLabel}
          {...axisProps}
        />
        <YAxis
          tickFormatter={(v) => compact(Number(v))}
          width={52}
          domain={["auto", "auto"]}
          {...axisProps}
        />
        <Tooltip
          content={<ChartTooltip unit={unit} />}
          cursor={{ stroke: chart.grid, strokeWidth: 1 }}
        />
        <Legend
          iconSize={8}
          wrapperStyle={{ fontSize: 12, color: chart.muted, paddingTop: 8 }}
        />

        <Area
          dataKey="value"
          stroke="none"
          fill="url(#valueFill)"
          legendType="none"
          {...noAnimation}
        />
        {hasInvested && (
          <Line
            dataKey="invested"
            stroke={chart.muted}
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            type="stepAfter"
            name="Investito"
            connectNulls
            {...noAnimation}
          />
        )}
        <Line
          dataKey="value"
          stroke={lineColor}
          strokeWidth={2}
          dot={false}
          name="Valore"
          {...noAnimation}
        />
        <Scatter dataKey="buy" fill="#ff6b81" name="Acquisto" {...noAnimation} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
