import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CandlestickChart, ChevronRight, Users, Coins, Settings2 } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const lots = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

function Stat({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-10 h-10 rounded-xl ${tint}`}><Icon size={18} /></div>
      <p className="text-2xl font-extrabold text-ink-900 mt-3 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400 mt-0.5">{label}</p>
    </div>
  );
}

export default function TradersLots() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [rate, setRate] = useState("");            // blank = use configured rate
  const [employee, setEmployee] = useState("");    // "" = all employees
  const [employees, setEmployees] = useState([]);
  const [open, setOpen] = useState({});            // employee_id -> bool

  useEffect(() => {
    api.get("/employees/").then((r) => {
      const list = r.data?.results || r.data || [];
      setEmployees(list.map((e) => ({ id: e.id, name: e.user_name || e.name })));
    }).catch(() => setEmployees([]));
  }, []);

  usePolling(() => {
    const params = { month, year };
    if (rate !== "") params.rate = rate;
    if (employee !== "") params.employee = employee;
    api.get("/reports/traders-lots/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load traders report."));
  }, 5000, [month, year, rate, employee]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading traders & lots…" />;

  const g = d.grand || {};
  const emps = d.employees || [];
  const toggle = (id) => setOpen((o) => ({ ...o, [id]: !o[id] }));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
            <CandlestickChart className="text-brand-600" /> Traders &amp; Lots
          </h1>
          <p className="text-sm text-ink-400">Har employee ke traders ne kitne lots trade kiye + estimated per-lot commission</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select className="input !w-auto" value={employee} onChange={(e) => setEmployee(e.target.value)}>
            <option value="">All employees</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
          <div className="flex items-center gap-1.5 chip !py-2" title="Per-lot commission rate">
            <Coins size={14} className="text-ink-400" />
            <input className="w-20 bg-transparent outline-none text-sm tabular-nums" type="number" step="0.01"
              placeholder={`${d.rate}/lot`} value={rate} onChange={(e) => setRate(e.target.value)} />
          </div>
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* grand totals */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Stat icon={Users} label="Traders" value={g.traders || 0} tint="bg-brand-100 text-brand-600" />
        <Stat icon={CandlestickChart} label={`Lots (${MONTHS[month - 1]})`} value={lots(g.lots_month)} tint="bg-violet-100 text-violet-600" />
        <Stat icon={Coins} label={`Commission (${MONTHS[month - 1]})`} value={money(g.commission_month)} tint="bg-emerald-100 text-emerald-600" />
        <Stat icon={CandlestickChart} label="Lots (all-time)" value={lots(g.lots_total)} tint="bg-ink-100 text-ink-500" />
        <Stat icon={Coins} label="Commission (all-time)" value={money(g.commission_total)} tint="bg-amber-100 text-amber-600" />
      </div>
      <p className="text-xs text-ink-400 -mt-2 flex flex-wrap items-center gap-1">
        Rate = <b className="text-ink-600">{money(d.rate)}</b> per lot — ye
        <Link to="/hr/payroll" className="inline-flex items-center gap-1 text-brand-600 font-medium hover:underline">
          <Settings2 size={12} /> Activity Incentives
        </Link>
        me set hoti hai (metric “Lots Traded”). Upar box me apni rate daal ke sirf preview badal sakte ho · Month = {MONTHS[month - 1]} {year}.
      </p>

      {/* employee → traders */}
      {emps.length === 0 && <EmptyState title="Koi lots data nahi" hint="FXArtha sync se lots aate hi yahaँ dikhega." />}
      <div className="space-y-3">
        {emps.map((e) => (
          <div key={e.employee_id} className="card overflow-hidden">
            <button onClick={() => toggle(e.employee_id)}
              className="w-full flex items-center gap-3 p-4 hover:bg-ink-50/60 text-left">
              <ChevronRight size={18} className={`text-ink-400 transition-transform ${open[e.employee_id] ? "rotate-90" : ""}`} />
              <div className="flex-1 min-w-0">
                <p className="font-bold text-ink-900 truncate">{e.name}</p>
                <p className="text-xs text-ink-400">{e.trader_count} trader{e.trader_count === 1 ? "" : "s"}</p>
              </div>
              <div className="hidden sm:flex items-center gap-6 text-right">
                <div><p className="text-[11px] text-ink-400 uppercase">Lots ({MONTHS[month - 1]})</p><p className="font-bold text-violet-600 tabular-nums">{lots(e.lots_month)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Comm ({MONTHS[month - 1]})</p><p className="font-bold text-emerald-600 tabular-nums">{money(e.commission_month)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Lots total</p><p className="font-bold text-ink-700 tabular-nums">{lots(e.lots_total)}</p></div>
                <div><p className="text-[11px] text-ink-400 uppercase">Comm total</p><p className="font-bold text-amber-600 tabular-nums">{money(e.commission_total)}</p></div>
              </div>
            </button>

            {open[e.employee_id] && (
              <div className="border-t border-ink-100 overflow-x-auto">
                <table className="w-full text-sm min-w-[560px]">
                  <thead>
                    <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                      <th className="py-2.5 px-4 font-semibold">Trader</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Lots ({MONTHS[month - 1]})</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Commission</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Lots (total)</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Commission (total)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.traders.map((t) => (
                      <tr key={t.customer_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                        <td className="py-2.5 px-4">
                          <Link to={`/customers/${t.customer_id}`} className="font-medium text-brand-700 hover:underline">{t.customer_name}</Link>
                        </td>
                        <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-violet-600">{lots(t.lots_month)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-emerald-600">{money(t.commission_month)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-ink-600">{lots(t.lots_total)}</td>
                        <td className="py-2.5 px-4 text-right tabular-nums text-amber-600">{money(t.commission_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
