import { useState, useEffect } from "react";
import { BarChart4, ChevronRight, ChevronDown } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const CAT = { growth: "text-emerald-600", activity: "text-blue-600", other: "text-ink-500" };

const fmt = (v, unit) => {
  const n = Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  return unit === "$" ? `$${n}` : unit && unit !== "count" ? `${n} ${unit}` : n;
};

function Row({ n, metrics, depth }) {
  const [open, setOpen] = useState(depth < 2);
  const hasKids = n.reports?.length > 0;
  return (
    <>
      <div className="flex items-center gap-2 py-2.5 border-b border-ink-100 hover:bg-ink-50/60"
        style={{ paddingLeft: `${depth * 20 + 8}px` }}>
        <button onClick={() => hasKids && setOpen(!open)} className={`text-ink-400 ${hasKids ? "" : "invisible"}`}>
          {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-ink-800 truncate">
            {n.name}
            {n.is_manager && <span className="ml-2 text-[10px] font-bold uppercase text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">team</span>}
          </p>
          {n.level && <p className="text-[11px] text-ink-400">{n.level}</p>}
        </div>
        {metrics.map((m) => (
          <div key={m.id} className="w-28 text-right text-sm text-ink-700 tabular-nums">
            {fmt(n.values[m.id], m.unit)}
          </div>
        ))}
      </div>
      {open && hasKids && n.reports.map((c) => <Row key={c.id} n={c} metrics={metrics} depth={depth + 1} />)}
    </>
  );
}

export default function KpiBoard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [businesses, setBusinesses] = useState([]);
  const [business, setBusiness] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  useEffect(() => {
    api.get("/businesses/").then((r) => setBusinesses(r.data.results || r.data)).catch(() => {});
  }, []);

  usePolling(() => {
    api.get("/reports/kpi-board/", { params: { month, year, business: business || undefined } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load KPI board."));
  }, 3000, [month, year, business]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading KPIs…" />;

  const metrics = d.metrics || [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><BarChart4 className="text-brand-600" /> KPI Board</h1>
          <p className="text-sm text-ink-400">Configurable KPIs · rolled up the org tree</p>
        </div>
        <div className="flex items-center gap-2">
          <select data-tour="kpi-business" className="input !w-auto" value={business} onChange={(e) => setBusiness(e.target.value)}>
            <option value="">All businesses</option>
            {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <select data-tour="kpi-period" className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {metrics.length === 0 ? (
        <EmptyState title="No KPIs defined" hint="Add metrics under Setup → KPI Definitions." />
      ) : (
        <div className="card p-5 overflow-x-auto">
          <div className="min-w-max">
            {/* header */}
            <div className="flex items-end gap-2 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
              <span className="flex-1 min-w-[180px]">Level / Person</span>
              {metrics.map((m) => (
                <span key={m.id} className="w-28 text-right">
                  <span className="block text-ink-700 normal-case text-xs font-bold truncate">{m.name}</span>
                  <span className={`${CAT[m.category] || "text-ink-400"} text-[10px]`}>{m.category} · {m.aggregation}</span>
                </span>
              ))}
            </div>
            {/* company totals */}
            <div className="flex items-center gap-2 py-2.5 border-b border-ink-200 bg-ink-50/40 px-2">
              <span className="flex-1 min-w-[180px] text-sm font-bold text-ink-800">Company total</span>
              {metrics.map((m) => (
                <span key={m.id} className="w-28 text-right text-sm font-bold text-ink-900 tabular-nums">{fmt(d.company[m.id], m.unit)}</span>
              ))}
            </div>
            {/* tree */}
            {d.tree?.length ? d.tree.map((n) => <Row key={n.id} n={n} metrics={metrics} depth={0} />)
              : <EmptyState title="No data" hint="No employees in the hierarchy yet." />}
          </div>
        </div>
      )}
    </div>
  );
}
