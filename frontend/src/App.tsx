import { useState } from "react";
import "./App.css";
import { usePortfolioSummary } from "./api/hooks";
import { money } from "./lib/format";
import { HoldingsView } from "./views/HoldingsView";
import { DashboardView } from "./views/DashboardView";
import { HistoryView } from "./views/HistoryView";
import { CompositionView } from "./views/CompositionView";
import { TransactionsView } from "./views/TransactionsView";
import { SimulationView } from "./views/SimulationView";

type Tab = "dashboard" | "holdings" | "history" | "composition" | "transactions" | "simulation";

// Dashboard first: it answers the question the app is opened for.
const TABS: { key: Tab; label: string }[] = [
  { key: "dashboard", label: "Dashboard" },
  { key: "holdings", label: "Strumenti" },
  { key: "history", label: "Storico" },
  { key: "composition", label: "Composizione" },
  { key: "transactions", label: "Transazioni" },
  { key: "simulation", label: "Simulazione" },
];

function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  // Shown in the header so the portfolio total is visible from any tab,
  // not only the dashboard.
  const { data: summary } = usePortfolioSummary();

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-bar">
          <div className="app-brand">
            <span className="app-brand-mark" aria-hidden="true">
              ◈
            </span>
            <h1>Finance Monitor</h1>
          </div>
          {summary && (
            <span className="app-meta">
              Portafoglio{" "}
              <strong style={{ color: "var(--text)" }}>
                {money(summary.total_value_base, summary.base_currency)}
              </strong>
            </span>
          )}
        </div>
        <nav className="app-nav">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              className={tab === t.key ? "active" : ""}
              onClick={() => setTab(t.key)}
              aria-current={tab === t.key ? "page" : undefined}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {tab === "dashboard" && <DashboardView />}
        {tab === "holdings" && <HoldingsView />}
        {tab === "history" && <HistoryView />}
        {tab === "composition" && <CompositionView />}
        {tab === "transactions" && <TransactionsView />}
        {tab === "simulation" && <SimulationView />}
      </main>
    </div>
  );
}

export default App;
