import { useState } from "react";
import { Coins, Play } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

export default function IncentiveBoard() {
  const { user } = useAuth();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [running, setRunning] = useState(false);
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  const canRun = user?.is_admin_view || ["Finance", "HR"].includes(user?.role_name);

  usePolling(() => {
    api.get("/reports/incentive-board/", { params: { month, year } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load incentive board."));
  }, 4000, [month, year]);

  const run = async () => {
    setRunning(true); setMsg("");
    try {
      const { data } = await api.post("/reports/incentive-run/", { month, year });
      setMsg(`Paid out ${money(data.grand_total)} · ${data.employees_credited} credited · ${data.payrolls_updated} payrolls updated.`);
    } catch {
      setMsg("Run failed.");
    } finally { setRunning(false); }
  };

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading incentives…" />;

  const rows = d.rows || [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Coins className="text-brand-600" /> Incentive Board</h1>
          <p className="text-sm text-ink-400">Target-slab + activity incentives · preview then run</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
          {canRun && (
            <button onClick={run} disabled={running}
              className="btn-primary flex items-center gap-1.5 disabled:opacity-50">
              <Play size={15} /> {running ? "Running…" : "Run payout"}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5"><p className="text-3xl font-extrabold text-brand-600 tabular-nums">{money(d.grand_total)}</p><p className="text-sm text-ink-400 mt-0.5">Total payout (this month)</p></div>
        <div className="card p-5 flex items-center"><p className="text-sm text-ink-500">{msg || "Preview shows what would be paid. “Run payout” writes it into Incentives + Payroll."}</p></div>
      </div>

      <div className="card p-5 overflow-x-auto">
        <div className="min-w-max">
          <div className="flex items-center gap-3 text-[11px] text-ink-400 font-semibold uppercase border-b border-ink-200 pb-2 px-2">
            <span className="flex-1 min-w-[160px]">Employee</span>
            <span className="w-20 text-right">Attain%</span>
            <span className="w-40">Slab</span>
            <span className="w-24 text-right">Slab $</span>
            <span className="flex-1 min-w-[200px]">Activity rewards</span>
            <span className="w-24 text-right">Total</span>
          </div>
          {rows.length ? rows.map((r) => (
            <div key={r.id} className="flex items-center gap-3 py-2.5 border-b border-ink-100 hover:bg-ink-50/60 px-2">
              <div className="flex-1 min-w-[160px]">
                <p className="text-sm font-semibold text-ink-800 truncate">{r.name}</p>
                {r.level && <p className="text-[11px] text-ink-400">{r.level}</p>}
              </div>
              <span className="w-20 text-right text-sm text-ink-600 tabular-nums">{r.attainment}%</span>
              <span className="w-40 text-[11px] text-ink-500 truncate">{r.slab || "—"}</span>
              <span className="w-24 text-right text-sm text-ink-700 tabular-nums">{money(r.slab_amount)}</span>
              <span className="flex-1 min-w-[200px] text-[11px] text-ink-500">
                {r.activities.length
                  ? r.activities.map((a) => `${a.name} (${a.count}×${money(a.rate)}=${money(a.amount)})`).join(", ")
                  : "—"}
              </span>
              <span className="w-24 text-right text-sm font-bold text-emerald-700 tabular-nums">{money(r.total)}</span>
            </div>
          )) : <EmptyState title="No incentives" hint="No revenue/activity to reward this month." />}
        </div>
      </div>
    </div>
  );
}
