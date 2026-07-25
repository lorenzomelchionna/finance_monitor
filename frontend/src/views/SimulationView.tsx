import { useEffect, useState, type FormEvent } from "react";
import { usePortfolioSummary, useRunMontecarlo } from "../api/hooks";
import { FanChart } from "../components/FanChart";
import { money } from "../lib/format";
import { extractErrorMessage } from "../lib/apiError";
import { parseLocaleNumber } from "../lib/number";

export function SimulationView() {
  const { data: summary } = usePortfolioSummary();
  const runMontecarlo = useRunMontecarlo();

  const [seedCapital, setSeedCapital] = useState("0");
  const [monthlyContribution, setMonthlyContribution] = useState("200");
  const [years, setYears] = useState("20");
  const [expectedReturn, setExpectedReturn] = useState("7");
  const [volatility, setVolatility] = useState("15");
  const [formError, setFormError] = useState<string | null>(null);

  // Prefill the seed with the current portfolio value once it loads —
  // per the plan's v1 scope: "seed = valore portafoglio attuale".
  useEffect(() => {
    if (summary && seedCapital === "0") {
      setSeedCapital(summary.total_value_base.toFixed(2));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summary]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

    const parsed = {
      seed_capital: parseLocaleNumber(seedCapital),
      monthly_contribution: parseLocaleNumber(monthlyContribution),
      years: parseLocaleNumber(years),
      expected_annual_return: parseLocaleNumber(expectedReturn) / 100,
      annual_volatility: parseLocaleNumber(volatility) / 100,
    };
    if (Object.values(parsed).some((v) => Number.isNaN(v))) {
      setFormError("Tutti i campi devono essere numeri validi.");
      return;
    }

    runMontecarlo.mutate(
      { ...parsed, n_paths: 10000 },
      { onError: (err) => setFormError(extractErrorMessage(err)) },
    );
  }

  const result = runMontecarlo.data;
  const totalContributed =
    (parseLocaleNumber(seedCapital) || 0) +
    (parseLocaleNumber(monthlyContribution) || 0) * (parseLocaleNumber(years) || 0) * 12;

  return (
    <div>
      <section className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <h2>Simulazione Monte Carlo — PAC</h2>
          </div>
        </div>
        <p className="panel-note">
          Proietta 10.000 possibili traiettorie di un piano di accumulo, assumendo rendimenti
          lognormali indipendenti. Le bande mostrano il ventaglio di esiti plausibili, non una
          previsione: la realtà ha code più spesse di questo modello.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span className="field-label">Capitale iniziale (EUR)</span>
              <input className="input" type="text" inputMode="decimal" value={seedCapital}
                onChange={(e) => setSeedCapital(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Contributo mensile (EUR)</span>
              <input className="input" type="text" inputMode="decimal" value={monthlyContribution}
                onChange={(e) => setMonthlyContribution(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Orizzonte (anni)</span>
              <input className="input" type="text" inputMode="numeric" value={years}
                onChange={(e) => setYears(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Rendimento atteso (% annuo)</span>
              <input className="input" type="text" inputMode="decimal" value={expectedReturn}
                onChange={(e) => setExpectedReturn(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Volatilità (% annua)</span>
              <input className="input" type="text" inputMode="decimal" value={volatility}
                onChange={(e) => setVolatility(e.target.value)} />
            </label>
            <div className="field">
              <span className="field-label" aria-hidden="true" />
              <button type="submit" className="btn btn-primary" disabled={runMontecarlo.isPending}>
                {runMontecarlo.isPending ? "Simulo…" : "Esegui simulazione"}
              </button>
            </div>
          </div>
        </form>

        {totalContributed > 0 && (
          <p className="placeholder" style={{ marginTop: "var(--s4)" }}>
            Verserai in tutto {money(totalContributed)} nell'orizzonte scelto.
          </p>
        )}
        {formError && <p className="error-banner" style={{ marginTop: "var(--s4)" }}>{formError}</p>}
      </section>

      {!result && !runMontecarlo.isPending && (
        <section className="panel">
          <div className="empty-state">
            <span className="empty-state-icon" aria-hidden="true">◷</span>
            <p className="empty-state-title">Nessuna simulazione</p>
            <p>Imposta i parametri qui sopra e premi "Esegui simulazione".</p>
          </div>
        </section>
      )}

      {result && (
        <>
          <section className="panel">
            <div className="panel-header">
              <div className="panel-title">
                <h2>Distribuzione a {years} anni</h2>
              </div>
              <span className="placeholder">su {money(totalContributed)} versati</span>
            </div>
            <div className="metric-grid">
              <div className="metric">
                <span className="metric-label">Mediana (p50)</span>
                <span className="metric-value">{money(result.final_median, "EUR", 0)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Scenario sfavorevole (p5)</span>
                <span className="metric-value">{money(result.final_p5, "EUR", 0)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Scenario favorevole (p95)</span>
                <span className="metric-value">{money(result.final_p95, "EUR", 0)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Media</span>
                <span className="metric-value">{money(result.final_mean, "EUR", 0)}</span>
              </div>
            </div>
            <p className="placeholder" style={{ marginTop: "var(--s4)" }}>
              Nel 90% delle traiettorie il valore finale cade fra {money(result.final_p5, "EUR", 0)} e{" "}
              {money(result.final_p95, "EUR", 0)}.
            </p>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div className="panel-title">
                <h2>Proiezione nel tempo</h2>
              </div>
            </div>
            <FanChart
              months={result.months}
              p5={result.p5}
              p25={result.p25}
              p50={result.p50}
              p75={result.p75}
              p95={result.p95}
            />
          </section>
        </>
      )}
    </div>
  );
}
