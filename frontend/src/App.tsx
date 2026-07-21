import { useState } from "react";
import "./App.css";
import { HoldingsView } from "./views/HoldingsView";
import { DashboardView } from "./views/DashboardView";
import { HistoryView } from "./views/HistoryView";
import { SimulationView } from "./views/SimulationView";

type Tab = "holdings" | "dashboard" | "history" | "simulation";

const TABS: { key: Tab; label: string }[] = [
  { key: "holdings", label: "Holdings" },
  { key: "dashboard", label: "Dashboard" },
  { key: "history", label: "Storico" },
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
        {tab === "history" && <HistoryView />}
        {tab === "simulation" && <SimulationView />}
      </main>
    </div>
  );
}

export default App;
