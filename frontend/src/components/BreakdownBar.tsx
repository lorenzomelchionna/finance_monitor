import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { axisProps, chart, SERIES_COLORS } from "../lib/chartTheme";
import { percent } from "../lib/format";

interface Slice {
  key: string;
  weight: number; // 0..1
}

interface TipProps {
  active?: boolean;
  payload?: { payload?: { name: string; value: number } }[];
}

function BarTooltip({ active, payload }: TipProps) {
  const d = active ? payload?.[0]?.payload : null;
  if (!d) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{d.name}</div>
      <div style={{ color: chart.accent }}>{percent(d.value / 100)}</div>
    </div>
  );
}

/** Horizontal bars rather than a pie: geography routinely has 10+
 * categories, where pie slices below ~5% become unreadable and the
 * legend does all the work anyway. */
export function BreakdownBar({ slices }: { slices: Slice[] }) {
  if (slices.length === 0) {
    return <p className="placeholder">Nessun dato. Usa "Aggiorna composizione".</p>;
  }

  const data = slices.map((s) => ({ name: s.key, value: s.weight * 100 }));
  const height = Math.max(160, data.length * 30 + 24);
  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 0, right: 44, bottom: 0, left: 0 }}
        barCategoryGap={6}
      >
        <CartesianGrid stroke={chart.grid} strokeDasharray="2 4" horizontal={false} />
        {/* Headroom so the value label at the end of the longest bar
            isn't clipped by the plot edge. */}
        <XAxis type="number" domain={[0, maxValue * 1.12]} hide />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          {...axisProps}
          tick={{ fill: chart.muted, fontSize: 12 }}
        />
        <Tooltip content={<BarTooltip />} cursor={{ fill: "rgba(160,107,255,0.08)" }} />
        <Bar dataKey="value" isAnimationActive={false} radius={[0, 3, 3, 0]} maxBarSize={18}>
          {data.map((entry, i) => (
            <Cell key={entry.name} fill={SERIES_COLORS[i % SERIES_COLORS.length]} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            fontSize={11}
            fill={chart.muted}
            formatter={(v) => percent(Number(v) / 100)}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
