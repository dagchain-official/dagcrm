import { useState } from "react";
import { Landmark, ChevronRight, ChevronDown } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

function Row({ n, depth }) {
  const [open, setOpen] = useState(depth < 2);
  const hasKids = n.reports?.length > 0;
  const net = n.net_new;
  return (
    <>
      <div className="flex items-center gap-2 py-2.5 border-b border-ink-100 hover:bg-ink-50/60" style={{ paddingLeft: `${depth * 20 + 8}px` }}>
        <button onClick={() => hasKids && setOpen(!open)} className={`text-ink-400 ${hasKids ? "" : "invisible"}`}>
          {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-ink-800 truncate">{n.name}{n.is_manager && <span className="ml-2 text-[10px] font-bold uppercase text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">team</span>}</p>
          {n.level && <p className="text-[11px] text-ink-400">{n.level}</p>}
        </div>
        <span className="w-28 text-right text-sm text-ink-500 tabular-nums">{money(n.existing)}</span>
        <span className="w-28 text-right text-sm text-emerald-600 tabular-nums">{money(n.new_deposits)}</span>
        <span className="w-28 text-right text-sm text-rose-500 tabular-nums">{money(n.withdrawals)}</span>
        <span className={`w-28 text-right text-sm font-bold tabular-nums ${net < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money(n.net_new)}</span>
        <span className="w-28 text-right text-sm font-bold text-ink-800 tabular-nums">{money(n.closing)}</span>
      </div>
      {open && hasKids && n.reports.map((c) => <Row key={c.id} n={c} depth={depth + 1} />)}
    </>
  );
}

export default function AumBoard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  usePolling(() => {
    api.get("/reports/aum-board/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load AUM board."));
  }, 4000, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading AUM…" />;
  const c = d.company || {};

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Landmark className="text-brand-600" /> AUM Board</h1>
          <p className="text-sm text-ink-400">Net New AUM = New Deposits − Withdrawals · rolled up the org tree</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>{MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>{[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}</select>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card p-4"><p className="text-2xl font-extrabold text-emerald-600 tabular-nums">{money(c.new_deposits)}</p><p className="text-xs text-ink-400 mt-0.5">New Deposits</p></div>
        <div className="card p-4"><p className="text-2xl font-extrabold text-rose-500 tabular-nums">{money(c.withdrawals)}</p><p className="text-xs text-ink-400 mt-0.5">Withdrawals</p></div>
        <div className="card p-4"><p className={`text-2xl font-extrabold tabular-nums ${(c.net_new || 0) < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money(c.net_new)}</p><p className="text-xs text-ink-400 mt-0.5">Net New AUM</p></div>
        <div className="card p-4"><p className="text-2xl font-extrabold text-ink-800 tabular-nums">{money(c.closing)}</p><p className="text-xs text-ink-400 mt-0.5">Closing AUM</p></div>
      </div>

      <div className="card p-5 overflow-x-auto">
        <div className="min-w-max">
          <div className="flex items-center gap-2 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
            <span className="flex-1 min-w-[180px]">Level / Person</span>
            <span className="w-28 text-right">Existing</span>
            <span className="w-28 text-right">New Dep.</span>
            <span className="w-28 text-right">Withdrawals</span>
            <span className="w-28 text-right">Net New</span>
            <span className="w-28 text-right">Closing</span>
          </div>
          {d.tree?.length ? d.tree.map((n) => <Row key={n.id} n={n} depth={0} />) : <EmptyState title="No data" hint="No AUM entries yet." />}
        </div>
      </div>
    </div>
  );
}
