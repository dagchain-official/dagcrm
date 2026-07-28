import { useState } from "react";
import { BarChart4 } from "lucide-react";
import ResourceTable from "./ResourceTable";
import KpiBoard from "./KpiBoard";
import Performance from "./Performance";
import KpiPerformance from "./KpiPerformance";
import { useAuth } from "../context/AuthContext";

const ALL_TABS = [
  { k: "board", l: "KPI Board" },
  { k: "auto", l: "Auto Performance" },
  { k: "entries", l: "KPI Entries" },
  { k: "performance", l: "Performance" },
];

export default function KpiHub() {
  const { can } = useAuth();
  // A manager (reports access) gets every tab; an RM / Sales Executive gets only
  // the two scoped views — their own KPI Board and Performance — so they never
  // see the team-wide Auto Performance or KPI-entry tools.
  const isManager = can("reports", "view");
  const TABS = isManager ? ALL_TABS : ALL_TABS.filter((t) => t.k === "board" || t.k === "performance");
  const [tab, setTab] = useState("board");
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
        <BarChart4 className="text-brand-600" /> KPI & Performance
      </h1>
      <div data-tour="kpi-tabs" className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit flex-wrap">
        {TABS.map((t) => (
          <button key={t.k} onClick={() => setTab(t.k)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${tab === t.k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
            {t.l}
          </button>
        ))}
      </div>
      {tab === "board" && <KpiBoard />}
      {tab === "auto" && <KpiPerformance />}
      {tab === "entries" && <ResourceTable resource="metric-entries" />}
      {tab === "performance" && <Performance />}
    </div>
  );
}
