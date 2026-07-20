import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#aa3bff", "#3bc9ff", "#ffb23b", "#3bff8f", "#ff3b6e", "#8f3bff"];

interface Props {
  exposure: Record<string, number>; // currency -> fraction (0..1)
}

/** Reusable pie chart for currency exposure — kept generic (label +
 * value pairs) so a future geo/sector breakdown chart can reuse it
 * once that data source lands (see plan's Roadmap). */
export function CurrencyExposurePie({ exposure }: Props) {
  const data = Object.entries(exposure).map(([currency, fraction]) => ({
    name: currency,
    value: fraction,
  }));

  if (data.length === 0) {
    return <p className="placeholder">Nessun dato di esposizione disponibile.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          outerRadius={90}
          isAnimationActive={false}
          label={({ name, value }) => `${name} ${((value as number) * 100).toFixed(0)}%`}
        >
          {data.map((entry, index) => (
            <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
