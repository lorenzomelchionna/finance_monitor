import { useState } from "react";
import { usePortfolioSummary, useRefreshPrices, useSetManualPrice } from "../api/hooks";
import { CurrencyExposurePie } from "../components/CurrencyExposurePie";
import { InfoTip } from "../components/InfoTip";
import { parseLocaleNumber } from "../lib/number";

const STATUS_LABEL: Record<string, string> = {
  ok: "auto",
  manual: "manuale",
  missing: "mancante",
};

const TIP = {
  value: "Valore di mercato attuale di tutte le posizioni, convertito nella valuta base ai prezzi correnti (o all'ultimo prezzo manuale).",
  invested: "Capitale effettivamente versato: somma dei controvalori d'acquisto più le commissioni, dai movimenti Fineco importati (al netto delle vendite).",
  pnl: "Profitto/perdita latente = Valore totale − Capitale investito. Non realizzato finché non vendi.",
  ret: "Rendimento semplice = P/L in percentuale sul capitale investito. NON annualizzato: è il guadagno totale sul periodo, qualunque sia la sua durata.",
  xirr: "Rendimento annualizzato money-weighted (XIRR): tiene conto di quanto tempo ogni versamento è rimasto investito. Su finestre brevi (<1 anno) tende a sovrastimare, perché annualizza un periodo corto.",
  quantity: "Numero di quote/azioni detenute.",
  currency: "Valuta in cui lo strumento è quotato.",
  price: "Fonte dell'ultimo prezzo: auto (da yfinance), manuale (inserito a mano) o mancante.",
  cost: "Capitale investito nella posizione. ✓ = derivato dai movimenti Fineco (esatto, commissioni incluse); altrimenti prezzo di carico inserito a mano.",
  posValue: "Valore di mercato attuale della posizione (quantità × prezzo corrente), in valuta base.",
  posPnl: "Profitto/perdita latente della posizione = Valore − Costo.",
  posXirr: "Rendimento annualizzato (XIRR) della singola posizione, dai suoi acquisti e dal valore attuale.",
};

export function DashboardView() {
  const { data: summary, isLoading, error } = usePortfolioSummary();
  const refreshPrices = useRefreshPrices();
  const setManualPrice = useSetManualPrice();

  const [manualEdits, setManualEdits] = useState<Record<number, string>>({});

  if (isLoading) return <p className="placeholder">Caricamento…</p>;
  if (error || !summary) return <p className="error-banner">Errore nel caricamento del riepilogo.</p>;

  const pnlClass = summary.total_pnl_base >= 0 ? "pnl-positive" : "pnl-negative";
  const simpleReturn =
    summary.total_cost_base > 0 ? summary.total_pnl_base / summary.total_cost_base : null;

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
            <span className="summary-label">
              Valore totale <InfoTip text={TIP.value} />
            </span>
            <span className="summary-value">{summary.total_value_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">
              Capitale investito <InfoTip text={TIP.invested} />
            </span>
            <span className="summary-value">{summary.total_cost_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">
              P/L <InfoTip text={TIP.pnl} />
            </span>
            <span className={`summary-value ${pnlClass}`}>{summary.total_pnl_base.toFixed(2)}</span>
          </div>
          <div className="summary-card">
            <span className="summary-label">
              Rendimento <InfoTip text={TIP.ret} />
            </span>
            <span
              className={`summary-value ${
                simpleReturn != null ? (simpleReturn >= 0 ? "pnl-positive" : "pnl-negative") : ""
              }`}
            >
              {simpleReturn != null ? `${(simpleReturn * 100).toFixed(1)}%` : "—"}
            </span>
          </div>
          <div className="summary-card">
            <span className="summary-label">
              Rend. annualizzato (XIRR) <InfoTip text={TIP.xirr} />
            </span>
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
              <th>Quantità <InfoTip text={TIP.quantity} /></th>
              <th>Valuta <InfoTip text={TIP.currency} /></th>
              <th>Prezzo <InfoTip text={TIP.price} /></th>
              <th>Costo <InfoTip text={TIP.cost} /></th>
              <th>Valore <InfoTip text={TIP.posValue} /></th>
              <th>P/L <InfoTip text={TIP.posPnl} /></th>
              <th>XIRR <InfoTip text={TIP.posXirr} /></th>
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
