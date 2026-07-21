import { useMemo, useState } from "react";
import { usePortfolioHistory } from "../api/hooks";
import { HistoryChart } from "../components/HistoryChart";
import {
  HORIZONS,
  movingAverage,
  sliceByHorizon,
  type Horizon,
  type TsPoint,
} from "../lib/timeseries";

// "portfolio" = aggregate; a number = a single instrument_id.
type Selection = "portfolio" | number;

const SMOOTHING_OPTIONS = [
  { label: "Nessuno", value: 1 },
  { label: "7 giorni", value: 7 },
  { label: "30 giorni", value: 30 },
  { label: "90 giorni", value: 90 },
];

export function HistoryView() {
  const { data, isLoading, error } = usePortfolioHistory();

  const [selection, setSelection] = useState<Selection>("portfolio");
  const [horizon, setHorizon] = useState<Horizon>("MAX");
  const [smoothing, setSmoothing] = useState<number>(1);

  const baseCurrency = data?.base_currency ?? "EUR";

  // Raw series for the current selection (portfolio aggregate or one
  // instrument), before horizon slicing / smoothing.
  const rawPoints: TsPoint[] = useMemo(() => {
    if (!data) return [];
    if (selection === "portfolio") {
      return data.portfolio.map((p) => ({ date: p.date, value: p.value }));
    }
    const series = data.series.find((s) => s.instrument_id === selection);
    return series ? series.points.map((p) => ({ date: p.date, value: p.close })) : [];
  }, [data, selection]);

  const points = useMemo(
    () => movingAverage(sliceByHorizon(rawPoints, horizon), smoothing),
    [rawPoints, horizon, smoothing],
  );

  const selectedName =
    selection === "portfolio"
      ? "Portafoglio"
      : data?.series.find((s) => s.instrument_id === selection)?.name ?? "";

  if (isLoading) {
    return <p className="placeholder">Caricamento storico… (può richiedere qualche secondo)</p>;
  }
  if (error || !data) {
    return <p className="error-banner">Errore nel caricamento dello storico.</p>;
  }

  return (
    <div>
      <section className="panel">
        <div className="dashboard-header">
          <h2>Storico — {selectedName}</h2>
          <span className="placeholder">
            {points.length > 0
              ? `${new Date(points[0].date).toLocaleDateString("it-IT")} → ${new Date(
                  points[points.length - 1].date,
                ).toLocaleDateString("it-IT")}`
              : ""}
          </span>
        </div>

        <div className="history-controls">
          <div className="control-group">
            <span className="control-label">Orizzonte</span>
            <div className="segmented">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  type="button"
                  className={horizon === h ? "active" : ""}
                  onClick={() => setHorizon(h)}
                >
                  {h}
                </button>
              ))}
            </div>
          </div>

          <div className="control-group">
            <span className="control-label">Smoothing (media mobile)</span>
            <div className="segmented">
              {SMOOTHING_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  className={smoothing === o.value ? "active" : ""}
                  onClick={() => setSmoothing(o.value)}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <HistoryChart
          points={points}
          unit={selection === "portfolio" ? baseCurrency : undefined}
        />
      </section>

      <section className="panel">
        <h2>Vista</h2>
        <div className="history-selector">
          <button
            type="button"
            className={selection === "portfolio" ? "chip active" : "chip"}
            onClick={() => setSelection("portfolio")}
          >
            📊 Portafoglio (aggregato)
          </button>
          {data.series.map((s) => (
            <button
              key={s.instrument_id}
              type="button"
              className={selection === s.instrument_id ? "chip active" : "chip"}
              onClick={() => setSelection(s.instrument_id)}
            >
              {s.name}
              {s.ticker ? ` (${s.ticker})` : ""}
            </button>
          ))}
        </div>

        {data.warnings.length > 0 && (
          <ul className="history-warnings">
            {data.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        )}
        <p className="placeholder">
          L'aggregato parte dalla data in cui tutti gli strumenti in portafoglio hanno dati; le viste
          per singolo prodotto mostrano invece l'intero storico disponibile.
        </p>
      </section>
    </div>
  );
}
