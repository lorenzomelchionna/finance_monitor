import { money, percent } from "../lib/format";

const COLORS = ["#a06bff", "#3bc9ff", "#f0b429", "#3ddc97", "#ff6b81", "#8f6bff", "#3bffd5"];

interface Slice {
  key: string;
  value: number;
}

/** A single stacked bar plus a legend, replacing the pie chart.
 *
 * A pie needs a full panel and reads poorly below ~5% slices; for
 * "what share is each holding" a stacked bar carries the same
 * information in a fraction of the height, and the legend can show the
 * actual amounts alongside the percentages. */
export function AllocationBar({
  slices,
  total,
  currency,
}: {
  slices: Slice[];
  total: number;
  currency: string;
}) {
  const sorted = [...slices].filter((s) => s.value > 0).sort((a, b) => b.value - a.value);

  if (sorted.length === 0 || total <= 0) {
    return <p className="placeholder">Nessuna posizione valorizzata.</p>;
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          height: 12,
          borderRadius: 6,
          overflow: "hidden",
          gap: 2,
          marginBottom: "var(--s4)",
        }}
      >
        {sorted.map((s, i) => (
          <div
            key={s.key}
            title={`${s.key}: ${percent(s.value / total)}`}
            style={{
              width: `${(s.value / total) * 100}%`,
              background: COLORS[i % COLORS.length],
            }}
          />
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--s3)" }}>
        {sorted.map((s, i) => (
          <div key={s.key} className="row" style={{ gap: "var(--s2)", flexWrap: "nowrap", minWidth: 0 }}>
            <span
              aria-hidden="true"
              style={{
                width: 8,
                height: 8,
                borderRadius: 2,
                background: COLORS[i % COLORS.length],
                flexShrink: 0,
              }}
            />
            <span style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 13 }}>
              {s.key}
            </span>
            <span
              style={{
                marginLeft: "auto",
                fontSize: 13,
                fontVariantNumeric: "tabular-nums",
                color: "var(--text-muted)",
                whiteSpace: "nowrap",
              }}
            >
              {percent(s.value / total)} · {money(s.value, currency, 0)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
