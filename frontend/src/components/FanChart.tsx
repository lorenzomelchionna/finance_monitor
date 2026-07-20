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

interface Props {
  months: number[];
  p5: number[];
  p25: number[];
  p50: number[];
  p75: number[];
  p95: number[];
}

/** Percentile "fan" chart: stacked transparent/translucent Area bands
 * (p5-p25, p25-p75, p75-p95) plus a solid median line. Recharts has no
 * native band-chart primitive, so each band is modeled as a delta
 * stacked on top of the previous one (classic stacked-area trick).
 *
 * Note: isAnimationActive is off on every series — Recharts' default
 * entrance animation never completes in this environment (observed on
 * CurrencyExposurePie too), leaving the chart blank. */
export function FanChart({ months, p5, p25, p50, p75, p95 }: Props) {
  const data = months.map((month, i) => ({
    month,
    p5: p5[i],
    band_5_25: p25[i] - p5[i],
    band_25_75: p75[i] - p25[i],
    band_75_95: p95[i] - p75[i],
    p50: p50[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
        <XAxis dataKey="month" tickFormatter={(m) => `${(m / 12).toFixed(0)}a`} />
        <YAxis tickFormatter={(v) => Number(v).toLocaleString()} width={80} />
        <Tooltip
          labelFormatter={(m) => `Mese ${m} (anno ${(Number(m) / 12).toFixed(1)})`}
          formatter={(value) => Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}
        />
        <Legend />
        <Area
          dataKey="p5"
          stackId="fan"
          stroke="none"
          fill="transparent"
          isAnimationActive={false}
          legendType="none"
        />
        <Area
          dataKey="band_5_25"
          stackId="fan"
          stroke="none"
          fill="#aa3bff"
          fillOpacity={0.12}
          isAnimationActive={false}
          name="p5–p25"
        />
        <Area
          dataKey="band_25_75"
          stackId="fan"
          stroke="none"
          fill="#aa3bff"
          fillOpacity={0.3}
          isAnimationActive={false}
          name="p25–p75"
        />
        <Area
          dataKey="band_75_95"
          stackId="fan"
          stroke="none"
          fill="#aa3bff"
          fillOpacity={0.12}
          isAnimationActive={false}
          name="p75–p95"
        />
        <Line
          dataKey="p50"
          stroke="#3bc9ff"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
          name="Mediana"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
