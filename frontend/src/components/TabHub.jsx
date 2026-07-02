import { useState } from "react";
import ResourceTable from "../pages/ResourceTable";

// Generic tabbed section. Each tab is either { resource: "key" } (renders the
// CRUD table) or { element: <Component/> } (a custom page). Only the active
// tab is rendered.
export default function TabHub({ title, icon: Icon, tabs }) {
  const [active, setActive] = useState(tabs[0].k);
  const cur = tabs.find((t) => t.k === active) || tabs[0];
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
        {Icon && <Icon className="text-brand-600" />} {title}
      </h1>
      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit flex-wrap">
        {tabs.map((t) => (
          <button key={t.k} onClick={() => setActive(t.k)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${active === t.k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
            {t.l}
          </button>
        ))}
      </div>
      {cur.resource ? <ResourceTable resource={cur.resource} /> : cur.element}
    </div>
  );
}
