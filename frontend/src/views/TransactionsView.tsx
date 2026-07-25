import { useMemo, useState } from "react";
import { useTransactions } from "../api/hooks";
import { ImportTransactions } from "../components/ImportTransactions";
import { amount, money, quantity, shortDate } from "../lib/format";

const SIGN_LABEL: Record<string, string> = { A: "Acquisto", V: "Vendita" };

export function TransactionsView() {
  const { data: transactions, isLoading, error } = useTransactions();
  const [filter, setFilter] = useState<number | "all">("all");

  // Instruments present in the ledger, for the filter dropdown.
  const instruments = useMemo(() => {
    if (!transactions) return [];
    const seen = new Map<number, string>();
    for (const t of transactions) if (!seen.has(t.instrument_id)) seen.set(t.instrument_id, t.name);
    return [...seen.entries()].map(([id, name]) => ({ id, name }));
  }, [transactions]);

  const rows = useMemo(() => {
    if (!transactions) return [];
    return filter === "all" ? transactions : transactions.filter((t) => t.instrument_id === filter);
  }, [transactions, filter]);

  const totals = useMemo(() => {
    let invested = 0;
    let commissions = 0;
    for (const t of rows) {
      const signed = t.sign === "A" ? t.gross_amount : -t.gross_amount;
      invested += signed;
      commissions += t.commissions;
    }
    return { invested, commissions, count: rows.length };
  }, [rows]);

  if (isLoading) return <p className="placeholder">Caricamento…</p>;
  if (error) return <p className="error-banner">Errore nel caricamento delle transazioni.</p>;

  return (
    <div>
      <section className="panel">
        <div className="panel-header"><div className="panel-title"><h2>Transazioni</h2></div></div>
        <ImportTransactions />

        {(!transactions || transactions.length === 0) && (
          <p className="placeholder">
            Nessuna transazione importata. Carica l'export "Movimenti Dossier Titoli" di Fineco qui sopra.
          </p>
        )}

        {transactions && transactions.length > 0 && (
          <>
            <div className="controls-row">
              <div className="control-group">
                <span className="control-label">Strumento</span>
                <div className="segmented">
                  <button
                    type="button"
                    className={filter === "all" ? "active" : ""}
                    onClick={() => setFilter("all")}
                  >
                    Tutti
                  </button>
                  {instruments.map((i) => (
                    <button
                      key={i.id}
                      type="button"
                      className={filter === i.id ? "active" : ""}
                      onClick={() => setFilter(i.id)}
                    >
                      {i.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="metric-grid">
              <div className="metric">
                <span className="metric-label">Operazioni</span>
                <span className="metric-value">{totals.count}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Investito netto</span>
                <span className="metric-value">{money(totals.invested)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Commissioni totali</span>
                <span className="metric-value">{money(totals.commissions)}</span>
              </div>
            </div>

            <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Strumento</th>
                  <th>Operazione</th>
                  <th className="num">Quantità</th>
                  <th className="num">Prezzo</th>
                  <th className="num">Controvalore</th>
                  <th className="num">Commissioni</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id}>
                    <td>{shortDate(t.trade_date)}</td>
                    <td>
                      {t.name}
                      {t.isin ? <span className="isin-hint"> {t.isin}</span> : null}
                    </td>
                    <td>
                      <span className={`badge ${t.sign === "A" ? "badge-ok" : "badge-manual"}`}>
                        {SIGN_LABEL[t.sign] ?? t.sign}
                      </span>
                    </td>
                    <td className="num">{quantity(t.quantity)}</td>
                    <td className="num">{amount(t.price)}</td>
                    <td className="num">{amount(t.gross_amount)}</td>
                    <td className="num">{t.commissions > 0 ? amount(t.commissions) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
