import { useState, type FormEvent } from "react";
import {
  useCreateHolding,
  useDeleteHolding,
  useHoldings,
  useUpdateHolding,
} from "../api/hooks";
import { HoldingsTable } from "../components/HoldingsTable";
import type { components } from "../api/schema";

type AssetClass = components["schemas"]["AssetClass"];

const ASSET_CLASSES: AssetClass[] = ["etf", "stock", "bond", "cash", "other"];

const emptyForm = {
  isin: "",
  ticker: "",
  name: "",
  currency: "EUR",
  assetClass: "etf" as AssetClass,
  quantity: "",
  avgCostPrice: "",
  costCurrency: "EUR",
};

export function HoldingsView() {
  const { data: holdings, isLoading, error } = useHoldings();
  const createHolding = useCreateHolding();
  const updateHolding = useUpdateHolding();
  const deleteHolding = useDeleteHolding();

  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);

  function set<K extends keyof typeof emptyForm>(key: K, value: (typeof emptyForm)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (!form.isin && !form.ticker) {
      setFormError("Serve almeno ISIN o ticker.");
      return;
    }
    if (!form.name || !form.quantity || !form.avgCostPrice) {
      setFormError("Nome, quantità e prezzo di carico sono obbligatori.");
      return;
    }

    try {
      await createHolding.mutateAsync({
        instrument: {
          isin: form.isin || undefined,
          ticker: form.ticker || undefined,
          name: form.name,
          currency: form.currency,
          asset_class: form.assetClass,
          auto_price_enabled: true,
        },
        quantity: Number(form.quantity),
        avg_cost_price: Number(form.avgCostPrice),
        cost_currency: form.costCurrency,
      });
      setForm(emptyForm);
    } catch {
      setFormError("Creazione posizione fallita. Controlla i dati inseriti.");
    }
  }

  return (
    <div>
      <section className="panel">
        <h2>Aggiungi posizione</h2>
        {formError && <p className="error-banner">{formError}</p>}
        <form className="holding-form" onSubmit={handleSubmit}>
          <label>
            ISIN
            <input value={form.isin} onChange={(e) => set("isin", e.target.value)} />
          </label>
          <label>
            Ticker
            <input value={form.ticker} onChange={(e) => set("ticker", e.target.value)} />
          </label>
          <label>
            Nome
            <input value={form.name} onChange={(e) => set("name", e.target.value)} />
          </label>
          <label>
            Valuta strumento
            <input value={form.currency} onChange={(e) => set("currency", e.target.value)} />
          </label>
          <label>
            Asset class
            <select
              value={form.assetClass}
              onChange={(e) => set("assetClass", e.target.value as AssetClass)}
            >
              {ASSET_CLASSES.map((ac) => (
                <option key={ac} value={ac}>
                  {ac}
                </option>
              ))}
            </select>
          </label>
          <label>
            Quantità
            <input
              type="number"
              min={0}
              step="any"
              value={form.quantity}
              onChange={(e) => set("quantity", e.target.value)}
            />
          </label>
          <label>
            Prezzo di carico
            <input
              type="number"
              min={0}
              step="any"
              value={form.avgCostPrice}
              onChange={(e) => set("avgCostPrice", e.target.value)}
            />
          </label>
          <label>
            Valuta carico
            <input value={form.costCurrency} onChange={(e) => set("costCurrency", e.target.value)} />
          </label>
          <button type="submit" disabled={createHolding.isPending}>
            {createHolding.isPending ? "Aggiungo…" : "Aggiungi"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Posizioni</h2>
        {isLoading && <p className="placeholder">Caricamento…</p>}
        {error && <p className="error-banner">Errore nel caricamento delle posizioni.</p>}
        {holdings && (
          <HoldingsTable
            holdings={holdings}
            onUpdateQuantity={(id, quantity) => updateHolding.mutate({ id, body: { quantity } })}
            onDelete={(id) => deleteHolding.mutate(id)}
          />
        )}
      </section>
    </div>
  );
}
