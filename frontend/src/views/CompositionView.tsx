import { useMemo, useState } from "react";
import { useComposition, useRefreshComposition } from "../api/hooks";
import { BreakdownBar } from "../components/BreakdownBar";

const DIM_LABEL: Record<string, string> = {
  geography: "Esposizione geografica",
  sector: "Esposizione settoriale",
};

// "portfolio" = aggregate; a number = a single instrument_id.
type Selection = "portfolio" | number;

export function CompositionView() {
  const { data, isLoading, error } = useComposition();
  const refresh = useRefreshComposition();
  const [selection, setSelection] = useState<Selection>("portfolio");

  const selected = useMemo(() => {
    if (!data || selection === "portfolio") return null;
    return data.instruments.find((i) => i.instrument_id === selection) ?? null;
  }, [data, selection]);

  const selectedName = selected ? selected.name : "Portafoglio";

  return (
    <div>
      <section className="panel">
        <div className="panel-header">
          <div className="panel-title"><h2>Composizione (look-through) — {selectedName}</h2></div>
          <button type="button" className="btn" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
            {refresh.isPending ? "Aggiorno…" : "Aggiorna composizione"}
          </button>
        </div>
        <p className="placeholder">
          Pesi geografici e settoriali ricavati per ISIN da JustETF (lista completa, non solo top-4).
          L'aggregato di portafoglio è pesato sul valore di mercato di ogni posizione. Fonte pubblica
          non ufficiale: verifica sui factsheet se ti servono precisi.
        </p>
        {refresh.data && refresh.data.failed.length > 0 && (
          <p className="error-banner">
            Fetch fallito per: {refresh.data.failed.join(", ")}. Riprova o inserisci a mano.
          </p>
        )}

        {data && (
          <div className="chip-row">
            <button
              type="button"
              className={selection === "portfolio" ? "chip active" : "chip"}
              onClick={() => setSelection("portfolio")}
            >
              Portafoglio (aggregato)
            </button>
            {data.instruments.map((i) => (
              <button
                key={i.instrument_id}
                type="button"
                className={selection === i.instrument_id ? "chip active" : "chip"}
                onClick={() => setSelection(i.instrument_id)}
              >
                {i.name}
                {i.ticker ? ` (${i.ticker})` : ""}
              </button>
            ))}
          </div>
        )}
      </section>

      {isLoading && <p className="placeholder">Caricamento…</p>}
      {error && <p className="error-banner">Errore nel caricamento della composizione.</p>}

      {data &&
        (["geography", "sector"] as const).map((dim) => {
          const slices = selected
            ? selected.dimensions[dim] ?? []
            : data.dimensions[dim] ?? [];
          const isPortfolio = selection === "portfolio";
          const coverage = data.coverage[dim] ?? 0;
          const missing = data.missing[dim] ?? [];
          return (
            <section className="panel" key={dim}>
              <div className="panel-header">
                <div className="panel-title"><h2>{DIM_LABEL[dim]}</h2></div>
                {isPortfolio && (
                  <span className="placeholder">copertura {(coverage * 100).toFixed(0)}%</span>
                )}
              </div>
              {slices.length === 0 ? (
                <p className="placeholder">
                  Nessun dato {dim === "geography" ? "geografico" : "settoriale"}
                  {dim === "sector" ? " (es. ETF obbligazionari non hanno settori azionari)." : "."}
                </p>
              ) : (
                <BreakdownBar slices={slices.map((s) => ({ key: s.key, weight: s.weight }))} />
              )}
              {isPortfolio && missing.length > 0 && (
                <p className="placeholder">
                  Escluso da questa dimensione: {missing.join(", ")}.
                </p>
              )}
            </section>
          );
        })}

      {data && data.instruments.length === 0 && (
        <section className="panel">
          <p className="placeholder">
            Nessun dato di composizione. Premi "Aggiorna composizione" per scaricarlo da JustETF.
          </p>
        </section>
      )}
    </div>
  );
}
