import { useMemo, useState } from "react";
import { useTransactions } from "../api/hooks";
import { ImportTransactions } from "../components/ImportTransactions";

const SIGN_LABEL: Record<string, string> = { A: "Acquisto", V: "Vendita" };

const eur = (v: number) => v.toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

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
        <h2>Transazioni</h2>
        <ImportTransactions />

        {(!transactions || transactions.length === 0) && (
          <p className="placeholder">
            Nessuna transazione importata. Carica l'export "Movimenti Dossier Titoli" di Fineco qui sopra.
          </p>
        )}

        {transactions && transactions.length > 0 && (
          <>
            <div className="history-controls">
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

            <div className="summary-cards">
              <div className="summary-card">
                <span className="summary-label">Operazioni</span>
                <span className="summary-value">{totals.count}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Investito netto</span>
                <span className="summary-value">{eur(totals.invested)} EUR</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Commissioni totali</span>
                <span className="summary-value">{eur(totals.commissions)} EUR</span>
              </div>
            </div>

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
                    <td>{new Date(t.trade_date).toLocaleDateString("it-IT")}</td>
                    <td>
                      {t.name}
                      {t.isin ? <span className="isin-hint"> {t.isin}</span> : null}
                    </td>
                    <td>
                      <span className={`status-badge status-${t.sign === "A" ? "ok" : "manual"}`}>
                        {SIGN_LABEL[t.sign] ?? t.sign}
                      </span>
                    </td>
                    <td className="num">{t.quantity}</td>
                    <td className="num">{eur(t.price)}</td>
                    <td className="num">{eur(t.gross_amount)}</td>
                    <td className="num">{t.commissions > 0 ? eur(t.commissions) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </div>
  );
}
