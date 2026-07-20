import { useState } from "react";
import "./App.css";
import { HoldingsView } from "./views/HoldingsView";
import { DashboardView } from "./views/DashboardView";

type Tab = "holdings" | "dashboard" | "simulation";

const TABS: { key: Tab; label: string }[] = [
  { key: "holdings", label: "Holdings" },
  { key: "dashboard", label: "Dashboard" },
  { key: "simulation", label: "Simulazione" },
];

function App() {
  const [tab, setTab] = useState<Tab>("holdings");

  return (
    <div className="app">
      <nav className="app-nav">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={tab === t.key ? "active" : ""}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="app-main">
        {tab === "holdings" && <HoldingsView />}
        {tab === "dashboard" && <DashboardView />}
        {tab === "simulation" && <p className="placeholder">Simulazione Monte Carlo — Fase 5.</p>}
      </main>
    </div>
  );
}

export default App;
