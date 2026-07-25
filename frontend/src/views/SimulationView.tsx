import { useEffect, useState, type FormEvent } from "react";
import { usePortfolioSummary, useRunMontecarlo } from "../api/hooks";
import { FanChart } from "../components/FanChart";
import { money, percent } from "../lib/format";
import { InfoTip } from "../components/InfoTip";
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
  const [fatTails, setFatTails] = useState(true);

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
      {
        ...parsed,
        n_paths: 10000,
        distribution: fatTails ? "student_t" : "normal",
        // ~5 df matches monthly equity returns empirically.
        degrees_of_freedom: 5,
      },
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
          Proietta 10.000 possibili traiettorie di un piano di accumulo. Le bande mostrano il
          ventaglio di esiti plausibili, non una previsione. Gli shock mensili sono indipendenti fra
          loro: il modello non riproduce i periodi in cui i cali si susseguono.
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

        <div className="controls-row" style={{ marginTop: "var(--s4)", marginBottom: 0 }}>
          <div className="control-group">
            <span className="control-label">Distribuzione degli shock</span>
            <div className="segmented">
              <button type="button" className={fatTails ? "active" : ""} onClick={() => setFatTails(true)}>
                Code grasse (t di Student)
              </button>
              <button type="button" className={!fatTails ? "active" : ""} onClick={() => setFatTails(false)}>
                Normale (GBM)
              </button>
            </div>
          </div>
        </div>

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
              <div className="panel-title"><h2>Rischio lungo il percorso</h2></div>
            </div>
            <div className="metric-grid">
              <div className="metric">
                <span className="metric-label">
                  Perdita max tipica <InfoTip text="Massima discesa da un picco, sulla traiettoria mediana. È il calo che con ogni probabilità dovrai sopportare almeno una volta." />
                </span>
                <span className="metric-value neg">−{percent(result.median_max_drawdown)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">
                  Perdita max sfavorevole <InfoTip text="Massima discesa da un picco nel 5% di scenari peggiori. Serve per capire se reggeresti emotivamente il piano." />
                </span>
                <span className="metric-value neg">−{percent(result.worst_max_drawdown)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">
                  Rischio di restare sotto <InfoTip text="Quota di traiettorie che finiscono sotto il totale versato: avresti fatto meglio a tenere i soldi fermi (in termini nominali)." />
                </span>
                <span className="metric-value">{percent(result.prob_below_contributed)}</span>
              </div>
            </div>
            <p className="placeholder" style={{ marginTop: "var(--s4)" }}>
              Il drawdown misura il calo del mercato lungo il percorso, non i versamenti. Le code grasse
              si vedono soprattutto qui: sul valore finale a 20 anni incidono poco, perché 240 shock
              mensili si mediano fra loro.
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
