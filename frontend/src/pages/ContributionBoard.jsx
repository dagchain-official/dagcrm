import { useState } from "react";
import { Scale, ChevronRight, ChevronDown } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const COLS = [
  ["brokerage", "Brokerage"], ["insurance", "Insurance"], ["staking", "Staking"],
  ["other", "Other"], ["trading_loss", "Trading loss"], ["deposit", "Deposit"],
];

function Row({ n, depth }) {
  const [open, setOpen] = useState(depth < 2);
  const hasKids = n.reports?.length > 0;
  return (
    <>
      <div className="flex items-center gap-2 py-2.5 border-b border-ink-100 hover:bg-ink-50/60" style={{ paddingLeft: `${depth * 20 + 8}px` }}>
        <button onClick={() => hasKids && setOpen(!open)} className={`text-ink-400 ${hasKids ? "" : "invisible"}`}>
          {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>
        <div className="flex-1 min-w-[160px]">
          <p className="text-sm font-semibold text-ink-800 truncate">{n.name}{n.is_manager && <span className="ml-2 text-[10px] font-bold uppercase text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">team</span>}</p>
          {n.level && <p className="text-[11px] text-ink-400">{n.level}</p>}
        </div>
        {COLS.map(([k]) => <span key={k} className="w-24 text-right text-sm text-ink-500 tabular-nums">{money(n.components[k])}</span>)}
        <span className={`w-28 text-right text-sm font-bold tabular-nums ${n.net_contribution < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money(n.net_contribution)}</span>
      </div>
      {open && hasKids && n.reports.map((c) => <Row key={c.id} n={c} depth={depth + 1} />)}
    </>
  );
}

export default function ContributionBoard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  usePolling(() => {
    api.get("/reports/contribution-board/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load contribution board."));
  }, 4000, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading contribution…" />;
  const w = d.weights || {};

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Scale className="text-brand-600" /> Business Contribution</h1>
          <p className="text-sm text-ink-400">Net = Σ component × weight (admin formula, editable)</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>{MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>{[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}</select>
        </div>
      </div>

      <div className="card p-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
        <span className="font-semibold text-ink-600">Formula:</span>
        {COLS.map(([k, label]) => <span key={k}>{label} × <b className="text-ink-700">{w[k]}</b></span>)}
        <span className="text-ink-400">(edit in Contribution Formula)</span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="card p-5"><p className={`text-3xl font-extrabold tabular-nums ${(d.company?.net_contribution || 0) < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money(d.company?.net_contribution)}</p><p className="text-sm text-ink-400 mt-0.5">Company Net Business Contribution</p></div>
      </div>

      <div className="card p-5 overflow-x-auto">
        <div className="min-w-max">
          <div className="flex items-center gap-2 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
            <span className="flex-1 min-w-[160px]">Level / Person</span>
            {COLS.map(([k, label]) => <span key={k} className="w-24 text-right">{label}</span>)}
            <span className="w-28 text-right">Net</span>
          </div>
          {d.tree?.length ? d.tree.map((n) => <Row key={n.id} n={n} depth={0} />) : <EmptyState title="No data" hint="No contribution entries yet." />}
        </div>
      </div>
    </div>
  );
}
