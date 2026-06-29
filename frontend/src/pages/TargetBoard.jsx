import { useState } from "react";
import { Gauge, ChevronRight, ChevronDown } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();

const barColor = (p) => (p >= 100 ? "bg-emerald-500" : p >= 60 ? "bg-amber-400" : "bg-rose-400");

function Row({ n, depth }) {
  const [open, setOpen] = useState(depth < 2);
  const hasKids = n.reports?.length > 0;
  return (
    <>
      <div className="flex items-center gap-2 py-2.5 border-b border-ink-100 hover:bg-ink-50/60"
        style={{ paddingLeft: `${depth * 22 + 8}px` }}>
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
        <div className="w-24 text-right text-sm text-ink-500 tabular-nums">{money(n.ctc)}</div>
        <div className="w-16 text-right text-sm text-ink-400 tabular-nums">×{n.multiplier}</div>
        <div className="w-28 text-right text-sm font-bold text-ink-800 tabular-nums">{money(n.target)}</div>
        <div className="w-28 text-right text-sm text-emerald-600 tabular-nums">{money(n.achieved)}</div>
        <div className="w-32">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full bg-ink-100 overflow-hidden">
              <div className={`h-full ${barColor(n.progress)}`} style={{ width: `${Math.min(100, n.progress)}%` }} />
            </div>
            <span className="w-9 text-right text-xs font-semibold text-ink-500 tabular-nums">{n.progress}%</span>
          </div>
        </div>
      </div>
      {open && hasKids && n.reports.map((c) => <Row key={c.id} n={c} depth={depth + 1} />)}
    </>
  );
}

export default function TargetBoard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  usePolling(() => {
    api.get("/reports/target-board/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load target board."));
  }, 3000, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading targets…" />;

  const c = d.company || {};

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Gauge className="text-brand-600" /> Target Board</h1>
          <p className="text-sm text-ink-400">Target = CTC × Multiplier · rolled up the org tree</p>
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
        <div className="card p-5"><p className="text-3xl font-extrabold text-ink-800 tabular-nums">{money(c.target)}</p><p className="text-sm text-ink-400 mt-0.5">Total Target</p></div>
        <div className="card p-5"><p className="text-3xl font-extrabold text-emerald-600 tabular-nums">{money(c.achieved)}</p><p className="text-sm text-ink-400 mt-0.5">Achieved</p></div>
        <div className="card p-5"><p className="text-3xl font-extrabold text-brand-600 tabular-nums">{c.progress || 0}%</p><p className="text-sm text-ink-400 mt-0.5">Attainment</p></div>
      </div>

      {/* tree */}
      <div className="card p-5">
        <div className="flex items-center gap-2 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
          <span className="flex-1">Level / Person</span>
          <span className="w-24 text-right">CTC</span>
          <span className="w-16 text-right">Mult.</span>
          <span className="w-28 text-right">Target</span>
          <span className="w-28 text-right">Achieved</span>
          <span className="w-32 text-right">Progress</span>
        </div>
        {d.tree?.length ? d.tree.map((n) => <Row key={n.id} n={n} depth={0} />)
          : <EmptyState title="No data" hint="No employees in the hierarchy yet." />}
      </div>
    </div>
  );
}
