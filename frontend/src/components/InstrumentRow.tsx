import { useState } from "react";
import type { InstrumentOut, PositionOut } from "../api/hooks";
import { amount, quantity } from "../lib/format";

interface Props {
  instrument: InstrumentOut;
  /** Derived position, or null when the instrument is excluded or fully sold. */
  position: PositionOut | null;
  onPatch: (patch: { name?: string; ticker?: string; included?: boolean }) => void;
}

/** One instrument: an include/exclude checkbox, editable name and ticker,
 * and the figures derived from its transactions (read-only — they come
 * from the broker export, not from typing). */
export function InstrumentRow({ instrument, position, onPatch }: Props) {
  const [name, setName] = useState(instrument.name);
  const [ticker, setTicker] = useState(instrument.ticker ?? "");

  const excluded = !instrument.included;

  return (
    <tr className={excluded ? "row-excluded" : ""}>
      <td>
        <input
          type="checkbox"
          checked={instrument.included}
          onChange={(e) => onPatch({ included: e.target.checked })}
          aria-label={`Includi ${instrument.name} nel portafoglio`}
        />
      </td>
      <td>
        <input
          type="text"
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => {
            const trimmed = name.trim();
            if (!trimmed) {
              setName(instrument.name);
              return;
            }
            if (trimmed !== instrument.name) onPatch({ name: trimmed });
          }}
        />
      </td>
      <td>
        <span className="isin-hint">{instrument.isin ?? "—"}</span>
      </td>
      <td>
        <input
          type="text"
          placeholder="es. VWCE.MI"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onBlur={() => {
            const trimmed = ticker.trim();
            if (trimmed !== (instrument.ticker ?? "")) onPatch({ ticker: trimmed });
          }}
        />
        {!instrument.ticker && <span className="hint-warn"> prezzi manuali</span>}
      </td>
      <td className="num">{position ? quantity(position.quantity) : "—"}</td>
      <td className="num">{position ? amount(position.avg_cost) : "—"}</td>
      <td className="num">{position ? amount(position.invested) : "—"}</td>
    </tr>
  );
}
