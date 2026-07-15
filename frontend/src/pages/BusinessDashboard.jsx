import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Building2, TrendingUp, Users, Landmark, DollarSign, Wallet,
  ArrowUpRight, ArrowDownRight, MoreHorizontal, Activity,
} from "lucide-react";
import { useState } from "react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const num = (v, unit) => {
  const n = Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  return unit === "$" ? `$${n}` : unit && unit !== "count" ? `${n} ${unit}` : n;
};
const catTint = {
  growth: "bg-emerald-100 text-emerald-600",
  activity: "bg-blue-100 text-blue-600",
  other: "bg-violet-100 text-violet-600",
};

function Stat({ icon: Icon, label, value, sub, color, positive = true }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div className={`grid place-items-center w-11 h-11 rounded-2xl ${color}`}><Icon size={20} /></div>
        <MoreHorizontal size={18} className="text-ink-300" />
      </div>
      <p className="text-3xl font-extrabold text-ink-900 mt-4 tabular-nums">{value}</p>
      <p className="text-sm text-ink-400 mt-0.5">{label}</p>
      {sub && (
        <p className={`flex items-center gap-1 text-xs font-semibold mt-3 ${positive ? "text-emerald-600" : "text-rose-500"}`}>
          {positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />} {sub}
        </p>
      )}
    </div>
  );
}

function CardHead({ title, action }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h3 className="font-bold text-ink-900">{title}</h3>
      {action || <MoreHorizontal size={18} className="text-ink-300" />}
    </div>
  );
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const _now = new Date();

export default function BusinessDashboard({ businessId }) {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  // KPI-card period: cumulative (default) | month | year | range
  const [period, setPeriod] = useState("cumulative");
  const [pMonth, setPMonth] = useState(_now.getMonth() + 1);
  const [pYear, setPYear] = useState(_now.getFullYear());
  const [pFrom, setPFrom] = useState("");
  const [pTo, setPTo] = useState("");

  usePolling(() => {
    const params = { business: businessId, period };
    if (period === "month") { params.month = pMonth; params.year = pYear; }
    if (period === "year") { params.year = pYear; }
    if (period === "range") { if (pFrom) params.from = pFrom; if (pTo) params.to = pTo; }
    api.get("/reports/business-dashboard/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load business dashboard."));
  }, 5000, [businessId, period, pMonth, pYear, pFrom, pTo]);

  if (err) return <EmptyState title="Error" hint={err} />;
  if (!d) return <Spinner label="Loading business…" />;

  const aum = d.aum;
  const kpis = d.kpis || [];
  // KPIs that share a unit make a meaningful mini bar chart (else just cards)
  const chartable = kpis.filter((k) => Number(k.value) > 0);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Building2 className="text-brand-600" /> {d.business.name}
        </h1>
        <p className="text-sm text-ink-400">Business unit overview · live data</p>
      </div>

      {/* headline stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Stat icon={DollarSign} label="Net Revenue" value={money(d.net_revenue)} sub={`Gross ${money(d.gross_revenue)}`} color="bg-emerald-100 text-emerald-600" />
        <Stat icon={TrendingUp} label="This Month" value={money(d.month_net_revenue)} sub="net revenue" color="bg-indigo-100 text-indigo-600" />
        <Stat icon={Users} label="Customers" value={d.customers} sub="active accounts" color="bg-rose-100 text-rose-500" />
        {aum
          ? <Stat icon={Landmark} label="Net New AUM" value={money(aum.net_new)} sub={`Closing ${money(aum.closing)}`} color="bg-amber-100 text-amber-600" positive={(aum.net_new || 0) >= 0} />
          : <Stat icon={Activity} label="Key Metrics" value={kpis.length} sub="tracked KPIs" color="bg-violet-100 text-violet-600" />}
      </div>

      {/* charts row */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* revenue trend area */}
        <div className="card p-5 lg:col-span-2">
          <CardHead title="Revenue Trend" action={<span className="text-xs font-semibold text-emerald-600 flex items-center gap-1"><TrendingUp size={14} /> {money(d.net_revenue)} total</span>} />
          {d.revenue_trend?.length ? (
            <ResponsiveContainer width="100%" height={230}>
              <AreaChart data={d.revenue_trend} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="bizg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => money(v)} />
                <Area type="monotone" dataKey="net" stroke="#6366f1" strokeWidth={2.5} fill="url(#bizg)" name="Net revenue" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[230px] grid place-items-center text-sm text-ink-400">No revenue recorded yet.</div>
          )}
        </div>

        {/* AUM panel or KPI mini-bar */}
        <div className="card p-5">
          {aum ? (
            <>
              <CardHead title="AUM" action={<Landmark size={18} className="text-ink-300" />} />
              <div className="space-y-3">
                {[
                  ["New Deposits", aum.new_deposits, "text-emerald-600"],
                  ["Withdrawals", aum.withdrawals, "text-rose-500"],
                  ["Net New AUM", aum.net_new, (aum.net_new || 0) < 0 ? "text-rose-600" : "text-emerald-700"],
                  ["Existing AUM", aum.existing, "text-ink-500"],
                ].map(([l, v, c]) => (
                  <div key={l} className="flex items-center justify-between">
                    <span className="text-sm text-ink-500">{l}</span>
                    <span className={`text-sm font-bold tabular-nums ${c}`}>{money(v)}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-3 border-t border-ink-100">
                  <span className="text-sm font-semibold text-ink-700">Closing AUM</span>
                  <span className="text-lg font-extrabold text-ink-900 tabular-nums">{money(aum.closing)}</span>
                </div>
              </div>
            </>
          ) : chartable.length ? (
            <>
              <CardHead title="Top KPIs" />
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={chartable.slice(0, 6)} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={80} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]} fill="#8b5cf6" barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : (
            <>
              <CardHead title="KPIs" />
              <div className="h-[210px] grid place-items-center text-center px-3">
                <div>
                  <p className="text-sm text-ink-600">No KPI data yet</p>
                  <p className="text-xs text-ink-400 mt-1">Define metrics for <b>{d.business.name}</b> in Setup → KPI Definitions, or connect its API.</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* configurable KPI cards */}
      {kpis.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">
              Key metrics — {d.business.name}
              <span className="ml-2 normal-case text-ink-300">
                ({period === "cumulative" ? "all-time" : period === "month" ? `${MONTHS[pMonth - 1]} ${pYear}` : period === "year" ? pYear : "date range"})
              </span>
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <select className="input !py-1.5 !w-auto text-sm" value={period} onChange={(e) => setPeriod(e.target.value)}>
                <option value="cumulative">Cumulative</option>
                <option value="month">Monthly</option>
                <option value="year">Yearly</option>
                <option value="range">Date range</option>
              </select>
              {period === "month" && (
                <>
                  <select className="input !py-1.5 !w-auto text-sm" value={pMonth} onChange={(e) => setPMonth(Number(e.target.value))}>
                    {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
                  </select>
                  <select className="input !py-1.5 !w-auto text-sm" value={pYear} onChange={(e) => setPYear(Number(e.target.value))}>
                    {[pYear - 1, pYear, pYear + 1].map((y) => <option key={y} value={y}>{y}</option>)}
                  </select>
                </>
              )}
              {period === "year" && (
                <select className="input !py-1.5 !w-auto text-sm" value={pYear} onChange={(e) => setPYear(Number(e.target.value))}>
                  {[pYear - 2, pYear - 1, pYear, pYear + 1].map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
              )}
              {period === "range" && (
                <>
                  <input type="date" className="input !py-1.5 !w-auto text-sm" value={pFrom} onChange={(e) => setPFrom(e.target.value)} />
                  <input type="date" className="input !py-1.5 !w-auto text-sm" value={pTo} onChange={(e) => setPTo(e.target.value)} />
                </>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {kpis.map((k) => (
              <div key={k.name} className="card p-5">
                <div className="flex items-start justify-between">
                  <div className={`grid place-items-center w-10 h-10 rounded-xl ${catTint[k.category] || "bg-ink-100 text-ink-500"}`}><Activity size={18} /></div>
                  <span className="text-[10px] uppercase font-semibold text-ink-300">{k.category}</span>
                </div>
                <p className="text-2xl font-extrabold text-ink-900 mt-3 tabular-nums">{num(k.value, k.unit)}</p>
                <p className="text-sm text-ink-400 mt-0.5">{k.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* top RMs table */}
      <div className="card p-5">
        <CardHead title="Top Relationship Managers" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 pr-4 font-semibold">S/N</th>
                <th className="pb-3 px-4 font-semibold">Name</th>
                <th className="pb-3 px-4 font-semibold text-right">Revenue ({d.business.name})</th>
              </tr>
            </thead>
            <tbody>
              {(d.top_reps || []).map((r, i) => (
                <tr key={i} className="border-t border-ink-100 hover:bg-ink-50/70">
                  <td className="py-3 pr-4 text-ink-400">{String(i + 1).padStart(2, "0")}</td>
                  <td className="py-3 px-4 font-medium text-ink-800">{r.name}</td>
                  <td className="py-3 px-4 text-right tabular-nums font-semibold text-emerald-600">{money(r.revenue)}</td>
                </tr>
              ))}
              {(!d.top_reps || d.top_reps.length === 0) && (
                <tr><td colSpan={3} className="py-6 text-center text-ink-400">No revenue attributed yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
