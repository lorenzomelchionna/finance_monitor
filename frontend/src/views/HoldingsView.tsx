import { useInstruments, usePositions, useResolveTickers, useUpdateInstrument } from "../api/hooks";
import { ImportTransactions } from "../components/ImportTransactions";
import { InfoTip } from "../components/InfoTip";
import { InstrumentRow } from "../components/InstrumentRow";

const TIP = {
  included:
    "Se attivo, lo strumento entra nel portafoglio: conta in Dashboard, Storico e Composizione. Escluderlo non cancella nulla — le sue transazioni restano.",
  ticker:
    "Simbolo di borsa per il recupero prezzi (es. VWCE.MI). L'export Fineco non lo contiene, quindi va indicato qui. Senza ticker i prezzi vanno inseriti a mano.",
  quantity: "Quantità detenuta, calcolata dalle transazioni importate (acquisti meno vendite).",
  avgCost: "Prezzo medio di carico per quota, calcolato dalle transazioni, commissioni incluse.",
  invested: "Capitale versato per questa posizione, commissioni incluse.",
};

export function HoldingsView() {
  const { data: instruments, isLoading, error } = useInstruments();
  const { data: positions } = usePositions();
  const updateInstrument = useUpdateInstrument();
  const resolveTickers = useResolveTickers();

  const missingTicker = (instruments ?? []).filter((i) => !i.ticker).length;

  // Positions exist only for included instruments with a live quantity;
  // index them so each row can show its derived figures.
  const positionByInstrument = new Map(
    (positions ?? []).map((p) => [p.instrument.id, p]),
  );

  const includedCount = (instruments ?? []).filter((i) => i.included).length;

  return (
    <div>
      <section className="panel">
        <h2>Strumenti</h2>
        <p className="placeholder">
          L'export Fineco è la fonte di verità: gli strumenti e le quantità vengono dalle
          transazioni importate, non si inseriscono a mano. Qui scegli quali contano nel
          portafoglio e indichi il ticker per il recupero prezzi.
        </p>
        <ImportTransactions />
      </section>

      <section className="panel">
        <div className="dashboard-header">
          <h2>Portafoglio</h2>
          <span className="placeholder">
            {instruments ? `${includedCount} di ${instruments.length} inclusi` : ""}
          </span>
        </div>

        {missingTicker > 0 && (
          <div className="import-box">
            <p className="placeholder">
              {missingTicker} strumenti senza ticker: i prezzi non si aggiornano da soli. Provo a
              ricavarlo dall'ISIN.
            </p>
            <button
              type="button"
              onClick={() => resolveTickers.mutate()}
              disabled={resolveTickers.isPending}
            >
              {resolveTickers.isPending ? "Cerco…" : "🔎 Trova ticker automaticamente"}
            </button>
          </div>
        )}
        {resolveTickers.data && (
          <p className="import-result">
            {Object.keys(resolveTickers.data.resolved).length > 0
              ? `Trovati: ${Object.entries(resolveTickers.data.resolved)
                  .map(([name, t]) => `${name} → ${t}`)
                  .join(", ")}. `
              : ""}
            {resolveTickers.data.unresolved.length > 0
              ? `Da inserire a mano (non coperti dalla fonte): ${resolveTickers.data.unresolved.join(", ")}.`
              : ""}
          </p>
        )}

        {isLoading && <p className="placeholder">Caricamento…</p>}
        {error && <p className="error-banner">Errore nel caricamento degli strumenti.</p>}

        {instruments && instruments.length === 0 && (
          <p className="placeholder">
            Nessuno strumento. Importa l'export "Movimenti Dossier Titoli" di Fineco qui sopra per
            popolare il portafoglio.
          </p>
        )}

        {instruments && instruments.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>
                  Includi <InfoTip text={TIP.included} />
                </th>
                <th>Strumento</th>
                <th>ISIN</th>
                <th>
                  Ticker <InfoTip text={TIP.ticker} />
                </th>
                <th className="num">
                  Quantità <InfoTip text={TIP.quantity} />
                </th>
                <th className="num">
                  Prezzo medio <InfoTip text={TIP.avgCost} />
                </th>
                <th className="num">
                  Investito <InfoTip text={TIP.invested} />
                </th>
              </tr>
            </thead>
            <tbody>
              {instruments.map((instrument) => (
                <InstrumentRow
                  key={instrument.id}
                  instrument={instrument}
                  position={positionByInstrument.get(instrument.id) ?? null}
                  onPatch={(patch) => updateInstrument.mutate({ id: instrument.id, ...patch })}
                />
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
