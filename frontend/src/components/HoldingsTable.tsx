import { useState } from "react";
import type { HoldingOut } from "../api/hooks";
import { parseLocaleNumber } from "../lib/number";

interface Props {
  holdings: HoldingOut[];
  onUpdateQuantity: (id: number, quantity: number) => void;
  onUpdateInstrument: (instrumentId: number, updates: { name: string; ticker?: string }) => void;
  onDelete: (id: number) => void;
}

/** Reusable holdings table: inline quantity/name/ticker edit + delete.
 * Extracted from HoldingsView so it can be reused (e.g. a read-only
 * variant on the future dashboard) without dragging the add-form/
 * mutations along. */
export function HoldingsTable({ holdings, onUpdateQuantity, onUpdateInstrument, onDelete }: Props) {
  if (holdings.length === 0) {
    return <p className="placeholder">Nessuna posizione ancora. Aggiungine una qui sopra.</p>;
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Strumento</th>
          <th>ISIN</th>
          <th>Ticker</th>
          <th>Quantità</th>
          <th>Prezzo carico</th>
          <th>Valuta carico</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {holdings.map((holding) => (
          <HoldingRow
            key={holding.id}
            holding={holding}
            onUpdateQuantity={onUpdateQuantity}
            onUpdateInstrument={onUpdateInstrument}
            onDelete={onDelete}
          />
        ))}
      </tbody>
    </table>
  );
}

function HoldingRow({
  holding,
  onUpdateQuantity,
  onUpdateInstrument,
  onDelete,
}: {
  holding: HoldingOut;
  onUpdateQuantity: (id: number, quantity: number) => void;
  onUpdateInstrument: (instrumentId: number, updates: { name: string; ticker?: string }) => void;
  onDelete: (id: number) => void;
}) {
  const [quantity, setQuantity] = useState(String(holding.quantity));
  const [name, setName] = useState(holding.instrument.name);
  const [ticker, setTicker] = useState(holding.instrument.ticker ?? "");

  return (
    <tr>
      <td>
        <input
          type="text"
          className="instrument-name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => {
            const trimmed = name.trim();
            if (!trimmed) {
              setName(holding.instrument.name);
              return;
            }
            if (trimmed !== holding.instrument.name) {
              onUpdateInstrument(holding.instrument.id, { name: trimmed });
            }
          }}
        />
      </td>
      <td>{holding.instrument.isin ?? "—"}</td>
      <td>
        <input
          type="text"
          className="instrument-ticker-input"
          placeholder="es. VWCE.MI"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onBlur={() => {
            const trimmed = ticker.trim();
            if (trimmed !== (holding.instrument.ticker ?? "")) {
              onUpdateInstrument(holding.instrument.id, { name: holding.instrument.name, ticker: trimmed });
            }
          }}
        />
      </td>
      <td>
        <input
          type="text"
          inputMode="decimal"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          onBlur={() => {
            const parsed = parseLocaleNumber(quantity);
            if (!Number.isNaN(parsed) && parsed > 0 && parsed !== holding.quantity) {
              onUpdateQuantity(holding.id, parsed);
            }
          }}
        />
      </td>
      <td>{holding.avg_cost_price}</td>
      <td>{holding.cost_currency}</td>
      <td>
        <button type="button" onClick={() => onDelete(holding.id)}>
          Elimina
        </button>
      </td>
    </tr>
  );
}
