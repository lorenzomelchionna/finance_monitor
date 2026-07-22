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

const COLORS = [
  "#aa3bff", "#3bc9ff", "#ffb23b", "#3bff8f", "#ff3b6e", "#8f6bff",
  "#3bffd5", "#ff8f3b", "#6e9bff", "#c0ff3b", "#ff3bd5", "#3b8fff", "#9aa0aa",
];

interface Slice {
  key: string;
  weight: number; // 0..1
}

/** Horizontal bar chart for a composition breakdown — clearer than a pie
 * when there are many categories (geography can be 10+). Sorted order is
 * whatever the caller passes (backend sorts desc). */
export function BreakdownBar({ slices }: { slices: Slice[] }) {
  if (slices.length === 0) {
    return <p className="placeholder">Nessun dato. Usa "Aggiorna composizione".</p>;
  }

  const data = slices.map((s) => ({ name: s.key, value: s.weight * 100 }));
  const height = Math.max(160, data.length * 34 + 24);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
        <CartesianGrid horizontal={false} strokeDasharray="3 3" opacity={0.2} />
        <XAxis type="number" domain={[0, "auto"]} tickFormatter={(v) => `${v}%`} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 13 }} />
        <Tooltip
          formatter={(value) => [`${Number(value).toFixed(1)}%`, "Peso"]}
          cursor={{ fill: "rgba(170,59,255,0.08)" }}
        />
        <Bar dataKey="value" isAnimationActive={false} radius={[0, 4, 4, 0]}>
          {data.map((entry, i) => (
            <Cell key={entry.name} fill={COLORS[i % COLORS.length]} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            fontSize={12}
            formatter={(v) => `${Number(v).toFixed(1)}%`}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
