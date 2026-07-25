import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { axisProps, chart, gridProps, noAnimation } from "../lib/chartTheme";
import { compact, money } from "../lib/format";

interface Props {
  months: number[];
  p5: number[];
  p25: number[];
  p50: number[];
  p75: number[];
  p95: number[];
}

interface TipProps {
  active?: boolean;
  label?: string | number;
  payload?: { payload?: Record<string, number> }[];
}

/** Bands are stored as deltas for stacking, so the tooltip has to
 * reconstruct the actual percentile values rather than show the raw
 * series — otherwise it would report band widths, not outcomes. */
function FanTooltip({ active, payload, label }: TipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;

  const months = Number(label);
  const rows: [string, number][] = [
    ["p95", d.p5 + d.band_5_25 + d.band_25_75 + d.band_75_95],
    ["p75", d.p5 + d.band_5_25 + d.band_25_75],
    ["mediana", d.p50],
    ["p25", d.p5 + d.band_5_25],
    ["p5", d.p5],
  ];

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">
        Anno {(months / 12).toFixed(1)}
      </div>
      {rows.map(([name, value]) => (
        <div key={name} style={{ color: name === "mediana" ? chart.accent : chart.muted }}>
          {name} {money(value, "EUR", 0)}
        </div>
      ))}
    </div>
  );
}

/** Percentile "fan": Recharts has no band primitive, so each band is a
 * delta stacked on the one below (classic stacked-area trick), with the
 * median drawn on top as a solid line. */
export function FanChart({ months, p5, p25, p50, p75, p95 }: Props) {
  const data = months.map((month, i) => ({
    month,
    p5: p5[i],
    band_5_25: p25[i] - p5[i],
    band_25_75: p75[i] - p25[i],
    band_75_95: p95[i] - p75[i],
    p50: p50[i],
  }));

  // One tick per year, thinned so a long horizon doesn't crowd the axis.
  const yearStep = Math.max(1, Math.ceil(months.length / 12 / 8));
  const ticks = months.filter((m) => m % (12 * yearStep) === 0);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid {...gridProps} />
        <XAxis
          dataKey="month"
          ticks={ticks}
          tickFormatter={(m) => `${Math.round(Number(m) / 12)}a`}
          {...axisProps}
        />
        <YAxis tickFormatter={(v) => compact(Number(v))} width={52} {...axisProps} />
        <Tooltip content={<FanTooltip />} cursor={{ stroke: chart.grid, strokeWidth: 1 }} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: 12, color: chart.muted, paddingTop: 8 }} />

        {/* Invisible base so the bands stack from p5 upward. */}
        <Area dataKey="p5" stackId="fan" stroke="none" fill="transparent" legendType="none" {...noAnimation} />
        <Area
          dataKey="band_5_25"
          stackId="fan"
          stroke="none"
          fill={chart.accent}
          fillOpacity={0.12}
          name="p5–p25"
          {...noAnimation}
        />
        <Area
          dataKey="band_25_75"
          stackId="fan"
          stroke="none"
          fill={chart.accent}
          fillOpacity={0.28}
          name="p25–p75"
          {...noAnimation}
        />
        <Area
          dataKey="band_75_95"
          stackId="fan"
          stroke="none"
          fill={chart.accent}
          fillOpacity={0.12}
          name="p75–p95"
          {...noAnimation}
        />
        <Line
          dataKey="p50"
          stroke={chart.accent}
          strokeWidth={2}
          dot={false}
          name="Mediana"
          {...noAnimation}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
