import { useState } from "react";
import { BarChart4 } from "lucide-react";
import ResourceTable from "./ResourceTable";
import KpiBoard from "./KpiBoard";
import Performance from "./Performance";
import KpiPerformance from "./KpiPerformance";

const TABS = [
  { k: "board", l: "KPI Board" },
  { k: "auto", l: "Auto Performance" },
  { k: "entries", l: "KPI Entries" },
  { k: "performance", l: "Performance" },
];

export default function KpiHub() {
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
