import { useState } from "react";
import { Trophy } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();

const scoreColor = (s) => (s >= 75 ? "text-emerald-600" : s >= 40 ? "text-amber-600" : "text-rose-500");
const barColor = (s) => (s >= 75 ? "bg-emerald-500" : s >= 40 ? "bg-amber-400" : "bg-rose-400");
const rankBadge = (r) =>
  r === 1 ? "bg-amber-100 text-amber-700" : r === 2 ? "bg-ink-200 text-ink-700" : r === 3 ? "bg-orange-100 text-orange-700" : "bg-ink-50 text-ink-400";

function Bar({ score }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-ink-100 overflow-hidden">
        <div className={`h-full ${barColor(score)}`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
      <span className={`w-10 text-right text-xs font-semibold tabular-nums ${scoreColor(score)}`}>{score}</span>
    </div>
  );
}

export default function Performance() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  usePolling(() => {
    api.get("/reports/performance/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load performance."));
  }, 3000, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading performance…" />;

  const rows = d.rows || [];
  const w = rows[0]?.weights;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Trophy className="text-brand-600" /> Performance</h1>
          <p className="text-sm text-ink-400">
            Revenue · Growth · Activity scorecards
            {w && <span className="ml-1">— weighted {w.revenue}/{w.growth}/{w.activity}</span>}
          </p>
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

      <div className="card p-5 overflow-x-auto">
        <div className="min-w-max">
          <div className="flex items-center gap-3 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
            <span className="w-8">#</span>
            <span className="flex-1 min-w-[180px]">Employee</span>
            <span className="w-40">Revenue</span>
            <span className="w-40">Growth</span>
            <span className="w-40">Activity</span>
            <span className="w-20 text-right">Overall</span>
          </div>
          {rows.length ? rows.map((r) => (
            <div key={r.id} className="flex items-center gap-3 py-2.5 border-b border-ink-100 hover:bg-ink-50/60 px-2">
              <span className={`w-8 h-6 grid place-items-center rounded-full text-xs font-bold ${rankBadge(r.rank)}`}>{r.rank}</span>
              <div className="flex-1 min-w-[180px]">
                <p className="text-sm font-semibold text-ink-800 truncate">{r.name}</p>
                {r.level && <p className="text-[11px] text-ink-400">{r.level}</p>}
              </div>
              <span className="w-40"><Bar score={r.revenue_score} /></span>
              <span className="w-40"><Bar score={r.growth_score} /></span>
              <span className="w-40"><Bar score={r.activity_score} /></span>
              <span className={`w-20 text-right text-lg font-extrabold tabular-nums ${scoreColor(r.overall)}`}>{r.overall}</span>
            </div>
          )) : <EmptyState title="No data" hint="No employees to score yet." />}
        </div>
      </div>
      <p className="text-xs text-ink-400 px-1">
        Scores are peer-normalised (0–100): the top performer on each signal scores 100. Revenue blends revenue
        generated with target attainment; Growth & Activity average their KPI categories (KPI Definitions).
      </p>
    </div>
  );
}
