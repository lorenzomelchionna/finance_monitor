import { useState } from "react";
import { usePortfolioSummary, useRefreshPrices, useSetManualPrice } from "../api/hooks";
import { CurrencyExposurePie } from "../components/CurrencyExposurePie";
import { parseLocaleNumber } from "../lib/number";

const STATUS_LABEL: Record<string, string> = {
  ok: "auto",
  manual: "manuale",
  missing: "mancante",
};

export function DashboardView() {
  const { data: summary, isLoading, error } = usePortfolioSummary();
  const refreshPrices = useRefreshPrices();
  const setManualPrice = useSetManualPrice();

  const [manualEdits, setManualEdits] = useState<Record<number, string>>({});

  if (isLoading) return <p className="placeholder">Caricamento…</p>;
  if (error || !summary) return <p className="error-banner">Errore nel caricamento del riepilogo.</p>;

  const pnlClass = summary.total_pnl_base >= 0 ? "pnl-positive" : "pnl-negative";

  return (
    <div>
      <section className="panel">
        <div className="dashboard-header">
          <h2>Riepilogo portafoglio ({summary.base_currency})</h2>
          <button type="button" onClick={() => refreshPrices.mutate()} disabled={refreshPrices.isPending}>
            {refreshPrices.isPending ? "Aggiorno…" : "Aggiorna prezzi"}
          </button>
        </div>

        <div className="summary-cards">
          <div className="summary-card">
            <span className="summary-label">Valore totale</span>
            <span className="summary-value">{summary.total_value_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Capitale investito</span>
            <span className="summary-value">{summary.total_cost_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">P/L</span>
            <span className={`summary-value ${pnlClass}`}>{summary.total_pnl_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">Rendimento (XIRR)</span>
            <span
              className={`summary-value ${
                summary.xirr != null ? (summary.xirr >= 0 ? "pnl-positive" : "pnl-negative") : ""
              }`}
            >
              {summary.xirr != null ? `${(summary.xirr * 100).toFixed(1)}%` : "—"}
            </span>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Esposizione valuta</h2>
        <CurrencyExposurePie exposure={summary.currency_exposure} />
      </section>

      <section className="panel">
        <h2>Posizioni</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Strumento</th>
              <th>Quantità</th>
              <th>Valuta</th>
              <th>Prezzo</th>
              <th>Costo</th>
              <th>Valore</th>
              <th>P/L</th>
              <th>XIRR</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {summary.positions.map((p) => {
              const needsManualPrice = p.exclusion_reason === "missing_price";
              return (
                <tr key={p.instrument_id}>
                  <td>{p.instrument_name}</td>
                  <td>{p.quantity}</td>
                  <td>{p.price_currency}</td>
                  <td>
                    <span className={`status-badge status-${p.price_status}`}>
                      {STATUS_LABEL[p.price_status] ?? p.price_status}
                    </span>
                  </td>
                  <td title={p.avg_cost_source === "transactions" ? "Da transazioni Fineco" : "Inserito manualmente"}>
                    {p.cost_base !== null ? p.cost_base.toFixed(2) : "—"}
                    {p.avg_cost_source === "transactions" && <span className="cost-src"> ✓</span>}
                  </td>
                  <td>{p.value_base !== null ? p.value_base.toFixed(2) : "—"}</td>
                  <td className={p.pnl_base !== null && p.pnl_base < 0 ? "pnl-negative" : "pnl-positive"}>
                    {p.pnl_base !== null ? p.pnl_base.toFixed(2) : "—"}
                  </td>
                  <td className={p.xirr != null ? (p.xirr >= 0 ? "pnl-positive" : "pnl-negative") : ""}>
                    {p.xirr != null ? `${(p.xirr * 100).toFixed(1)}%` : "—"}
                  </td>
                  <td>
                    {needsManualPrice && (
                      <span className="manual-price-input">
                        <input
                          type="text"
                          inputMode="decimal"
                          placeholder="prezzo"
                          value={manualEdits[p.instrument_id] ?? ""}
                          onChange={(e) =>
                            setManualEdits((m) => ({ ...m, [p.instrument_id]: e.target.value }))
                          }
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const value = parseLocaleNumber(manualEdits[p.instrument_id] ?? "");
                            if (!Number.isNaN(value) && value > 0) {
                              setManualPrice.mutate({
                                instrumentId: p.instrument_id,
                                price: value,
                                currency: p.price_currency,
                              });
                            }
                          }}
                        >
                          Imposta
                        </button>
                      </span>
                    )}
                    {p.exclusion_reason === "missing_fx" && (
                      <span className="placeholder">cambio non disponibile</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
