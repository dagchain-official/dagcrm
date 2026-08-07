import { useEffect, useState } from "react";
import { TrendingUp, Users, DollarSign, Wallet, Target, ChevronRight, AlertTriangle } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

function Stat({ icon: Icon, label, value, tint, sub }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-10 h-10 rounded-xl ${tint}`}><Icon size={18} /></div>
      <p className="text-2xl font-extrabold text-ink-900 mt-3 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400 mt-0.5">{label}</p>
      {sub && <p className="text-[11px] text-ink-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function TeamPnl() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [open, setOpen] = useState({});

  useEffect(() => {
    setD(null); setErr("");
    api.get("/reports/team-pnl/", { params: { month, year } })
      .then((r) => setD(r.data))
      .catch((e) => setErr(e.response?.status === 403 ? "This dashboard is for Super Admin, Finance and Business Heads only." : "Failed to load."));
  }, [month, year]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading Team P&L…" />;

  const t = d.totals || {};
  const toggle = (id) => setOpen((o) => ({ ...o, [id]: !o[id] }));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><TrendingUp className="text-brand-600" /> Team P&amp;L</h1>
          <p className="text-sm text-ink-400">Each team's CTC vs revenue — profit, and how much more revenue reaches profitability.</p>
        </div>
        <div className="flex gap-2">
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* company totals */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={Wallet} label="Total Team CTC" value={money(t.team_ctc)} tint="bg-violet-100 text-violet-600" sub={`${t.teams} teams`} />
        <Stat icon={DollarSign} label="Revenue Generated" value={money(t.revenue)} tint="bg-emerald-100 text-emerald-600" />
        <Stat icon={TrendingUp} label="Profit / (Loss)" value={money(t.profit)} tint={t.profit >= 0 ? "bg-emerald-100 text-emerald-600" : "bg-rose-100 text-rose-500"} />
        <Stat icon={AlertTriangle} label="Revenue to Profit" value={money(t.gap_to_profit)} tint="bg-amber-100 text-amber-600" sub="more revenue needed" />
      </div>

      {/* per team */}
      {d.rows.length === 0 ? <EmptyState title="No teams" hint="No team leaders in your scope." /> : (
        <div className="space-y-3">
          {d.rows.map((r) => (
            <div key={r.employee_id} className="card overflow-hidden">
              <button onClick={() => toggle(r.employee_id)} className="w-full flex flex-wrap items-center gap-3 p-4 hover:bg-ink-50/60 text-left">
                <ChevronRight size={18} className={`text-ink-400 transition-transform ${open[r.employee_id] ? "rotate-90" : ""}`} />
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-ink-900 truncate">{r.team_leader}</p>
                  <p className="text-xs text-ink-400">{r.member_count} member{r.member_count === 1 ? "" : "s"} · TL salary {money(r.tl_salary)}</p>
                </div>
                <div className="hidden sm:flex items-center gap-6 text-right">
                  <div><p className="text-[11px] text-ink-400 uppercase">Team CTC</p><p className="font-bold text-violet-600 tabular-nums">{money(r.team_ctc)}</p></div>
                  <div><p className="text-[11px] text-ink-400 uppercase">Revenue</p><p className="font-bold text-emerald-600 tabular-nums">{money(r.revenue)}</p></div>
                  <div><p className="text-[11px] text-ink-400 uppercase">Profit</p><p className={`font-bold tabular-nums ${r.profit >= 0 ? "text-emerald-600" : "text-rose-500"}`}>{money(r.profit)}</p></div>
                  <div><p className="text-[11px] text-ink-400 uppercase">To profit</p><p className="font-bold text-amber-600 tabular-nums">{r.gap_to_profit > 0 ? money(r.gap_to_profit) : "✓ profitable"}</p></div>
                </div>
              </button>
              {open[r.employee_id] && (
                <div className="border-t border-ink-100 overflow-x-auto">
                  <table className="w-full text-sm min-w-[480px]">
                    <thead>
                      <tr className="text-left text-ink-400 text-[11px] uppercase bg-ink-50">
                        <th className="py-2.5 px-4 font-semibold">Member</th>
                        <th className="py-2.5 px-4 font-semibold">Role</th>
                        <th className="py-2.5 px-4 font-semibold text-right">CTC</th>
                        <th className="py-2.5 px-4 font-semibold text-right">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.members.map((m, i) => (
                        <tr key={i} className="border-t border-ink-100">
                          <td className="py-2.5 px-4 font-medium text-ink-800">{m.name}</td>
                          <td className="py-2.5 px-4 text-ink-500">{m.role}</td>
                          <td className="py-2.5 px-4 text-right tabular-nums text-violet-600">{money(m.ctc)}</td>
                          <td className="py-2.5 px-4 text-right tabular-nums text-emerald-600">{money(m.revenue)}</td>
                        </tr>
                      ))}
                      {r.members.length === 0 && <tr><td colSpan={4} className="py-4 text-center text-ink-400">No members.</td></tr>}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
