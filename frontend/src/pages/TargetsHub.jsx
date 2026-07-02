import { useState } from "react";
import { Crosshair } from "lucide-react";
import ResourceTable from "./ResourceTable";
import TargetBoard from "./TargetBoard";
import AssignTarget from "./AssignTarget";

const TABS = [
  { k: "targets", l: "Targets" },
  { k: "board", l: "Target Board" },
  { k: "assign", l: "Assign Target" },
];

export default function TargetsHub() {
  const [tab, setTab] = useState("targets");
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
        <Crosshair className="text-brand-600" /> Targets
      </h1>
      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit">
        {TABS.map((t) => (
          <button key={t.k} onClick={() => setTab(t.k)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${tab === t.k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
            {t.l}
          </button>
        ))}
      </div>
      {tab === "targets" && <ResourceTable resource="targets" />}
      {tab === "board" && <TargetBoard />}
      {tab === "assign" && <AssignTarget />}
    </div>
  );
}
