import { useEffect, useState } from "react";
import { Network, Users2, Layers3, ChevronRight } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";

const initials = (name) =>
  (name || "?").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

// Colour a node by its hierarchy level (falls back to a neutral tint).
const LEVEL_TINTS = [
  "bg-brand-100 text-brand-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-violet-100 text-violet-700",
  "bg-sky-100 text-sky-700",
  "bg-rose-100 text-rose-600",
];
const tintFor = (level) => {
  if (!level) return "bg-ink-100 text-ink-500";
  let h = 0;
  for (const c of level) h = (h + c.charCodeAt(0)) % LEVEL_TINTS.length;
  return LEVEL_TINTS[h];
};

function Node({ n }) {
  const [open, setOpen] = useState(true);
  const hasKids = n.children?.length > 0;
  return (
    <div>
      <div className="flex items-center gap-3 card p-3 hover:shadow-soft transition">
        {hasKids ? (
          <button onClick={() => setOpen((o) => !o)}
            className="grid place-items-center w-6 h-6 rounded-lg text-ink-400 hover:bg-ink-100 shrink-0">
            <ChevronRight size={16} className={`transition ${open ? "rotate-90" : ""}`} />
          </button>
        ) : (
          <span className="w-6 shrink-0" />
        )}
        <div className={`grid place-items-center w-9 h-9 rounded-xl font-bold text-xs shrink-0 ${tintFor(n.level)}`}>
          {initials(n.name)}
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-ink-900 truncate">{n.name}</p>
          <p className="text-xs text-ink-400 truncate">
            {n.level || n.role || "—"}{n.designation ? ` · ${n.designation}` : ""}
          </p>
        </div>
        {n.reports > 0 && (
          <span className="ml-auto badge bg-ink-100 text-ink-500 shrink-0">
            {n.reports} report{n.reports !== 1 ? "s" : ""}
          </span>
        )}
      </div>
      {hasKids && open && (
        <div className="ml-5 mt-2 pl-4 border-l-2 border-ink-100 space-y-2">
          {n.children.map((c) => <Node key={c.id} n={c} />)}
        </div>
      )}
    </div>
  );
}

export default function HierarchyTree() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/reports/hierarchy/")
      .then((r) => setD(r.data))
      .catch(() => setErr("Failed to load the org hierarchy."));
  }, []);

  if (err) return <EmptyState title="Not available" hint={err} />;
  if (!d) return <Spinner label="Loading hierarchy…" />;

  const levels = new Set();
  const walk = (n) => { if (n.level) levels.add(n.level); (n.children || []).forEach(walk); };
  (d.tree || []).forEach(walk);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Network className="text-brand-600" /> Org Hierarchy
        </h1>
        <p className="text-sm text-ink-400">Who reports to whom — built from each employee's manager.</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="card p-4">
          <div className="grid place-items-center w-9 h-9 rounded-xl bg-brand-100 text-brand-600"><Users2 size={18} /></div>
          <p className="text-2xl font-extrabold text-ink-900 mt-2">{d.total}</p>
          <p className="text-xs text-ink-400">People in the org</p>
        </div>
        <div className="card p-4">
          <div className="grid place-items-center w-9 h-9 rounded-xl bg-violet-100 text-violet-600"><Layers3 size={18} /></div>
          <p className="text-2xl font-extrabold text-ink-900 mt-2">{levels.size}</p>
          <p className="text-xs text-ink-400">Hierarchy levels</p>
        </div>
        <div className="card p-4">
          <div className="grid place-items-center w-9 h-9 rounded-xl bg-emerald-100 text-emerald-600"><Network size={18} /></div>
          <p className="text-2xl font-extrabold text-ink-900 mt-2">{(d.tree || []).length}</p>
          <p className="text-xs text-ink-400">Top-level heads</p>
        </div>
      </div>

      {(d.tree || []).length === 0 ? (
        <EmptyState title="No hierarchy yet" hint="Add employees and set each one's manager to build the tree." />
      ) : (
        <div className="space-y-3">
          {d.tree.map((n) => <Node key={n.id} n={n} />)}
        </div>
      )}
    </div>
  );
}
