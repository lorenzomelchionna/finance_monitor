import { useState } from "react";
import { usePortfolioSummary, useRefreshPrices, useSetManualPrice } from "../api/hooks";
import { AllocationBar } from "../components/AllocationBar";
import { InfoTip } from "../components/InfoTip";
import { amount, money, percent, signedMoney, signedPercent, quantity, toneOf } from "../lib/format";
import { parseLocaleNumber } from "../lib/number";

const PRICE_BADGE: Record<string, { label: string; cls: string }> = {
  ok: { label: "auto", cls: "badge-ok" },
  manual: { label: "manuale", cls: "badge-manual" },
  missing: { label: "mancante", cls: "badge-missing" },
};

const TIP = {
  invested:
    "Capitale effettivamente versato: controvalori d'acquisto più commissioni, dalle transazioni importate (al netto delle vendite).",
  pnl: "Profitto/perdita latente = Valore totale − Capitale investito. Non realizzato finché non vendi.",
  ret: "Rendimento semplice = P/L in percentuale sul capitale investito. NON annualizzato: è il guadagno totale sul periodo, qualunque ne sia la durata.",
  xirr: "Rendimento annualizzato money-weighted (XIRR): tiene conto di quanto tempo ogni versamento è rimasto investito. Su finestre brevi (<1 anno) tende a sovrastimare.",
  quantity: "Quote detenute, calcolate dalle transazioni importate.",
  price:
    "Fonte dell'ultimo prezzo: auto (yfinance), manuale (inserito a mano) o mancante (serve un ticker o un prezzo).",
  cost: "Capitale investito nella posizione, commissioni incluse.",
  value: "Valore di mercato attuale: quantità × prezzo corrente.",
  pnlPos: "Profitto/perdita latente della posizione = Valore − Costo.",
  retPos: "Rendimento semplice della posizione = P/L sul suo costo. Non annualizzato.",
  xirrPos: "Rendimento annualizzato (XIRR) della posizione, dai suoi acquisti e dal valore attuale.",
  weight: "Peso della posizione sul valore totale del portafoglio.",
};

export function DashboardView() {
  const { data: summary, isLoading, error } = usePortfolioSummary();
  const refreshPrices = useRefreshPrices();
  const setManualPrice = useSetManualPrice();
  const [manualEdits, setManualEdits] = useState<Record<number, string>>({});

  if (isLoading) {
    return (
      <section className="panel">
        <div className="stack">
          <div className="skeleton" style={{ width: "40%", height: 40 }} />
          <div className="skeleton" style={{ width: "70%" }} />
          <div className="skeleton" style={{ width: "55%" }} />
        </div>
      </section>
    );
  }
  if (error || !summary) {
    return <p className="error-banner">Errore nel caricamento del riepilogo.</p>;
  }

  const base = summary.base_currency;
  const invested = summary.total_cost_base;
  const simpleReturn = invested > 0 ? summary.total_pnl_base / invested : null;
  const pnlTone = toneOf(summary.total_pnl_base);

  const priced = summary.positions.filter((p) => p.value_base !== null);
  const needsAttention = summary.positions.filter((p) => p.price_status === "missing");

  if (summary.positions.length === 0) {
    return (
      <section className="panel">
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            ◈
          </span>
          <p className="empty-state-title">Nessuna posizione</p>
          <p>Importa l'export Fineco dal tab Strumenti per popolare il portafoglio.</p>
        </div>
      </section>
    );
  }

  return (
    <div>
      <section className="panel">
        <div className="metric-hero">
          <div>
            <div className="metric-label">Valore totale</div>
            <div className="metric-hero-value">{money(summary.total_value_base, base)}</div>
            <div className={`metric-hero-delta ${pnlTone}`}>
              <span>{signedMoney(summary.total_pnl_base, base)}</span>
              {simpleReturn != null && <span>({signedPercent(simpleReturn)})</span>}
            </div>
          </div>
          <button
            type="button"
            className="btn"
            onClick={() => refreshPrices.mutate()}
            disabled={refreshPrices.isPending}
          >
            {refreshPrices.isPending ? "Aggiorno…" : "↻ Aggiorna prezzi"}
          </button>
        </div>

        <div className="metric-grid">
          <div className="metric">
            <span className="metric-label">
              Capitale investito <InfoTip text={TIP.invested} />
            </span>
            <span className="metric-value">{money(invested, base)}</span>
          </div>
          <div className="metric">
            <span className="metric-label">
              P/L latente <InfoTip text={TIP.pnl} />
            </span>
            <span className={`metric-value ${pnlTone}`}>
              {signedMoney(summary.total_pnl_base, base)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">
              Rendimento <InfoTip text={TIP.ret} />
            </span>
            <span className={`metric-value ${toneOf(simpleReturn)}`}>
              {simpleReturn != null ? signedPercent(simpleReturn) : "—"}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">
              Annualizzato (XIRR) <InfoTip text={TIP.xirr} />
            </span>
            <span className={`metric-value ${toneOf(summary.xirr)}`}>
              {summary.xirr != null ? signedPercent(summary.xirr) : "—"}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Posizioni</span>
            <span className="metric-value">{summary.positions.length}</span>
          </div>
        </div>
      </section>

      {needsAttention.length > 0 && (
        <div className="notice">
          <span aria-hidden="true">⚠</span>
          <span>
            {needsAttention.length === 1
              ? `${needsAttention[0].instrument_name} non ha un prezzo: è escluso dai totali.`
              : `${needsAttention.length} posizioni senza prezzo: sono escluse dai totali.`}{" "}
            Imposta un ticker in Strumenti, oppure un prezzo manuale qui sotto.
          </span>
        </div>
      )}

      {/* The old currency pie rendered a single 100% slice for a
          single-currency portfolio — a whole panel for no information.
          Allocation by position is what actually varies. */}
      <section className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <h2>Allocazione</h2>
          </div>
          <span className="placeholder">
            {Object.keys(summary.currency_exposure).length > 1
              ? Object.entries(summary.currency_exposure)
                  .map(([ccy, f]) => `${ccy} ${percent(f, 0)}`)
                  .join(" · ")
              : `100% ${base}`}
          </span>
        </div>
        <AllocationBar
          slices={priced.map((p) => ({
            key: p.instrument_name,
            value: p.value_base as number,
          }))}
          total={summary.total_value_base}
          currency={base}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <h2>Posizioni</h2>
          </div>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Strumento</th>
                <th className="num">
                  <span className="th-inner">
                    Quantità <InfoTip text={TIP.quantity} />
                  </span>
                </th>
                <th>
                  <span className="th-inner">
                    Prezzo <InfoTip text={TIP.price} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    Costo <InfoTip text={TIP.cost} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    Valore <InfoTip text={TIP.value} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    Peso <InfoTip text={TIP.weight} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    P/L <InfoTip text={TIP.pnlPos} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    Rend. <InfoTip text={TIP.retPos} />
                  </span>
                </th>
                <th className="num">
                  <span className="th-inner">
                    XIRR <InfoTip text={TIP.xirrPos} />
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.positions.map((p) => {
                const badge = PRICE_BADGE[p.price_status] ?? PRICE_BADGE.missing;
                const posReturn =
                  p.pnl_base != null && p.cost_base != null && p.cost_base > 0
                    ? p.pnl_base / p.cost_base
                    : null;
                const weight =
                  p.value_base != null && summary.total_value_base > 0
                    ? p.value_base / summary.total_value_base
                    : null;

                return (
                  <tr key={p.instrument_id}>
                    <td>
                      <span className="cell-primary">{p.instrument_name}</span>
                      <span className="cell-sub">{p.price_currency}</span>
                    </td>
                    <td className="num">{quantity(p.quantity)}</td>
                    <td>
                      <span className={`badge ${badge.cls}`}>{badge.label}</span>
                      {p.price_status === "missing" && (
                        <span className="row" style={{ marginTop: 6 }}>
                          <input
                            className="input"
                            type="text"
                            inputMode="decimal"
                            placeholder="prezzo"
                            style={{ width: 90 }}
                            value={manualEdits[p.instrument_id] ?? ""}
                            onChange={(e) =>
                              setManualEdits((m) => ({ ...m, [p.instrument_id]: e.target.value }))
                            }
                          />
                          <button
                            type="button"
                            className="btn btn-sm"
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
                            Salva
                          </button>
                        </span>
                      )}
                    </td>
                    <td className="num">{p.cost_base != null ? amount(p.cost_base) : "—"}</td>
                    <td className="num">{p.value_base != null ? amount(p.value_base) : "—"}</td>
                    <td className="num">{weight != null ? percent(weight, 1) : "—"}</td>
                    <td className={`num ${toneOf(p.pnl_base)}`}>
                      {p.pnl_base != null ? signedMoney(p.pnl_base, base) : "—"}
                    </td>
                    <td className={`num ${toneOf(posReturn)}`}>
                      {posReturn != null ? signedPercent(posReturn) : "—"}
                    </td>
                    <td className={`num ${toneOf(p.xirr)}`}>
                      {p.xirr != null ? signedPercent(p.xirr) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
