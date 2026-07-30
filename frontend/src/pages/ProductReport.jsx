import { useState } from "react";
import { Package } from "lucide-react";
import TradersLots from "./TradersLots";
import DagChainByRm from "./DagChainByRm";

// One place to see the per-employee client book by platform. FX Artha = each
// employee's traders with lots + commission; DAGChain = their users with nodes,
// revenue, commission, rewards. Both views are the existing reports, reused.
export default function ProductReport() {
  const [tab, setTab] = useState("fxartha");
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Package className="text-brand-600" /> Product Report
        </h1>
        <p className="text-sm text-ink-400">Each employee's clients with full lots / nodes, commission and everything — pick a platform.</p>
      </div>
      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit">
        {[["fxartha", "FX Artha"], ["dagchain", "DAGChain"]].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition ${tab === k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
            {l}
          </button>
        ))}
      </div>
      {tab === "fxartha" ? <TradersLots /> : <DagChainByRm />}
    </div>
  );
}
