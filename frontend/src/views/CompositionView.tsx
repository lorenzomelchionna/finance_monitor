import { useComposition, useRefreshComposition } from "../api/hooks";
import { BreakdownBar } from "../components/BreakdownBar";

const DIM_LABEL: Record<string, string> = {
  geography: "Esposizione geografica",
  sector: "Esposizione settoriale",
};

export function CompositionView() {
  const { data, isLoading, error } = useComposition();
  const refresh = useRefreshComposition();

  return (
    <div>
      <section className="panel">
        <div className="dashboard-header">
          <h2>Composizione (look-through)</h2>
          <button type="button" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
            {refresh.isPending ? "Aggiorno…" : "Aggiorna composizione"}
          </button>
        </div>
        <p className="placeholder">
          Pesi geografici e settoriali aggregati sul portafoglio, ricavati per ISIN da JustETF e
          pesati sul valore di mercato di ogni posizione. Fonte pubblica non ufficiale: verifica i
          valori sui factsheet se ti servono precisi.
        </p>
        {refresh.data && refresh.data.failed.length > 0 && (
          <p className="error-banner">
            Fetch fallito per: {refresh.data.failed.join(", ")}. Riprova o inserisci a mano.
          </p>
        )}
      </section>

      {isLoading && <p className="placeholder">Caricamento…</p>}
      {error && <p className="error-banner">Errore nel caricamento della composizione.</p>}

      {data &&
        (["geography", "sector"] as const).map((dim) => {
          const slices = data.dimensions[dim] ?? [];
          const coverage = data.coverage[dim] ?? 0;
          const missing = data.missing[dim] ?? [];
          return (
            <section className="panel" key={dim}>
              <div className="dashboard-header">
                <h2>{DIM_LABEL[dim]}</h2>
                <span className="placeholder">copertura {(coverage * 100).toFixed(0)}%</span>
              </div>
              <BreakdownBar slices={slices.map((s) => ({ key: s.key, weight: s.weight }))} />
              {missing.length > 0 && (
                <p className="placeholder">
                  Senza dati {dim === "geography" ? "geografici" : "settoriali"}: {missing.join(", ")}
                  {dim === "sector" ? " (es. ETF obbligazionari non hanno settori azionari)." : "."}
                </p>
              )}
            </section>
          );
        })}

      {data && Object.keys(data.dimensions).length === 0 && (
        <section className="panel">
          <p className="placeholder">
            Nessun dato di composizione. Premi "Aggiorna composizione" per scaricarlo da JustETF.
          </p>
        </section>
      )}
    </div>
  );
}
