import { useEffect, useState, type FormEvent } from "react";
import { usePortfolioSummary, useRunMontecarlo } from "../api/hooks";
import { FanChart } from "../components/FanChart";

export function SimulationView() {
  const { data: summary } = usePortfolioSummary();
  const runMontecarlo = useRunMontecarlo();

  const [seedCapital, setSeedCapital] = useState("0");
  const [monthlyContribution, setMonthlyContribution] = useState("200");
  const [years, setYears] = useState("20");
  const [expectedReturn, setExpectedReturn] = useState("7");
  const [volatility, setVolatility] = useState("15");

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
    runMontecarlo.mutate({
      seed_capital: Number(seedCapital),
      monthly_contribution: Number(monthlyContribution),
      years: Number(years),
      expected_annual_return: Number(expectedReturn) / 100,
      annual_volatility: Number(volatility) / 100,
      n_paths: 10000,
    });
  }

  const result = runMontecarlo.data;

  return (
    <div>
      <section className="panel">
        <h2>Simulazione Monte Carlo — PAC</h2>
        <form className="holding-form" onSubmit={handleSubmit}>
          <label>
            Capitale iniziale (EUR)
            <input type="number" min={0} step="any" value={seedCapital} onChange={(e) => setSeedCapital(e.target.value)} />
          </label>
          <label>
            Contributo mensile (EUR)
            <input
              type="number"
              min={0}
              step="any"
              value={monthlyContribution}
              onChange={(e) => setMonthlyContribution(e.target.value)}
            />
          </label>
          <label>
            Orizzonte (anni)
            <input type="number" min={1} max={60} value={years} onChange={(e) => setYears(e.target.value)} />
          </label>
          <label>
            Rendimento atteso (% annuo)
            <input type="number" step="any" value={expectedReturn} onChange={(e) => setExpectedReturn(e.target.value)} />
          </label>
          <label>
            Volatilità (% annua)
            <input type="number" min={0} step="any" value={volatility} onChange={(e) => setVolatility(e.target.value)} />
          </label>
          <button type="submit" disabled={runMontecarlo.isPending}>
            {runMontecarlo.isPending ? "Simulo…" : "Esegui simulazione"}
          </button>
        </form>
        {runMontecarlo.isError && (
          <p className="error-banner">Simulazione fallita. Controlla i parametri.</p>
        )}
      </section>

      {result && (
        <>
          <section className="panel">
            <h2>Distribuzione finale</h2>
            <div className="summary-cards">
              <div className="summary-card">
                <span className="summary-label">Mediana</span>
                <span className="summary-value">{result.final_median.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Media</span>
                <span className="summary-value">{result.final_mean.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">P5 – P95</span>
                <span className="summary-value">
                  {result.final_p5.toLocaleString(undefined, { maximumFractionDigits: 0 })} –{" "}
                  {result.final_p95.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>Proiezione nel tempo</h2>
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
