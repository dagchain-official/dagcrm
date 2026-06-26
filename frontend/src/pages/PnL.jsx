import { useState } from "react";
import { TrendingUp, ChevronRight, ChevronDown, Wallet } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();

function Row({ n, depth }) {
  const [open, setOpen] = useState(depth < 2);
  const hasKids = n.reports?.length > 0;
  const loss = n.profit < 0;
  return (
    <>
      <div className="flex items-center gap-2 py-2.5 border-b border-ink-100 hover:bg-ink-50/60"
        style={{ paddingLeft: `${depth * 22 + 8}px` }}>
        <button onClick={() => hasKids && setOpen(!open)} className={`text-ink-400 ${hasKids ? "" : "invisible"}`}>
          {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-ink-800 truncate">{n.name}</p>
          {n.level && <p className="text-[11px] text-ink-400">{n.level}</p>}
        </div>
        <div className="w-28 text-right text-sm text-emerald-600 tabular-nums">{money(n.revenue)}</div>
        <div className="w-28 text-right text-sm text-rose-500 tabular-nums">{money(n.cost)}</div>
        <div className={`w-28 text-right text-sm font-bold tabular-nums ${loss ? "text-rose-600" : "text-emerald-700"}`}>
          {loss ? "−" : ""}{money(Math.abs(n.profit))}
        </div>
        <div className="w-16 text-right text-xs text-ink-400 tabular-nums">{n.margin}%</div>
      </div>
      {open && hasKids && n.reports.map((c) => <Row key={c.id} n={c} depth={depth + 1} />)}
    </>
  );
}

export default function PnL() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  usePolling(() => {
    api.get("/reports/pnl/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch((e) => setErr(e.response?.status === 403 ? "P&L is available to managers, Finance and admins." : "Failed to load."));
  }, 3000, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading P&L…" />;

  const c = d.company || {};
  const loss = (c.profit || 0) < 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><TrendingUp className="text-brand-600" /> P&amp;L Statement</h1>
          <p className="text-sm text-ink-400">Revenue − Cost per hierarchy level</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* company totals */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-5"><p className="text-3xl font-extrabold text-emerald-600 tabular-nums">{money(c.revenue)}</p><p className="text-sm text-ink-400 mt-0.5">Revenue</p></div>
        <div className="card p-5"><p className="text-3xl font-extrabold text-rose-500 tabular-nums">{money(c.cost)}</p><p className="text-sm text-ink-400 mt-0.5">Cost (CTC)</p></div>
        <div className="card p-5"><p className={`text-3xl font-extrabold tabular-nums ${loss ? "text-rose-600" : "text-emerald-700"}`}>{loss ? "−" : ""}{money(Math.abs(c.profit))}</p><p className="text-sm text-ink-400 mt-0.5">{loss ? "Loss" : "Profit"}</p></div>
      </div>

      {/* tree */}
      <div className="card p-5">
        <div className="flex items-center gap-2 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
          <span className="flex-1">Level / Person</span>
          <span className="w-28 text-right">Revenue</span>
          <span className="w-28 text-right">Cost</span>
          <span className="w-28 text-right">Profit</span>
          <span className="w-16 text-right">Margin</span>
        </div>
        {d.tree?.length ? d.tree.map((n) => <Row key={n.id} n={n} depth={0} />)
          : <EmptyState title="No data" hint="No employees in the hierarchy yet." />}
        {d.unattributed_revenue > 0 && (
          <div className="flex items-center gap-2 py-2.5 mt-1 text-ink-500" style={{ paddingLeft: "8px" }}>
            <Wallet size={15} className="text-ink-300" />
            <span className="flex-1 text-sm italic">Unattributed revenue (no lead owner)</span>
            <span className="w-28 text-right text-sm text-emerald-600 tabular-nums">{money(d.unattributed_revenue)}</span>
            <span className="w-28" /><span className="w-28" /><span className="w-16" />
          </div>
        )}
      </div>
    </div>
  );
}
