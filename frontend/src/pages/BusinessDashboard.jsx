import { useState } from "react";
import { Building2, TrendingUp, Users, Landmark } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const num = (v, unit) => {
  const n = Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  return unit === "$" ? `$${n}` : unit && unit !== "count" ? `${n} ${unit}` : n;
};
const catColor = { growth: "text-emerald-600", activity: "text-blue-600", other: "text-violet-600" };

export default function BusinessDashboard({ businessId }) {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");

  usePolling(() => {
    api.get("/reports/business-dashboard/", { params: { business: businessId } })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load business dashboard."));
  }, 4000, [businessId]);

  if (err) return <EmptyState title="Error" hint={err} />;
  if (!d) return <Spinner label="Loading business…" />;

  const maxTrend = Math.max(...(d.revenue_trend || []).map((t) => t.net), 1);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Building2 className="text-brand-600" /> {d.business.name}
        </h1>
        <p className="text-sm text-ink-400">Business unit overview · live data</p>
      </div>

      {/* headline cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5"><p className="text-2xl font-extrabold text-emerald-600 tabular-nums">{money(d.net_revenue)}</p><p className="text-sm text-ink-400 mt-0.5">Net revenue</p></div>
        <div className="card p-5"><p className="text-2xl font-extrabold text-ink-800 tabular-nums">{money(d.gross_revenue)}</p><p className="text-sm text-ink-400 mt-0.5">Gross revenue</p></div>
        <div className="card p-5"><p className="text-2xl font-extrabold text-brand-600 tabular-nums">{money(d.month_net_revenue)}</p><p className="text-sm text-ink-400 mt-0.5">This month</p></div>
        <div className="card p-5"><p className="text-2xl font-extrabold text-ink-800 tabular-nums flex items-center gap-1"><Users size={18} className="text-ink-400" />{d.customers}</p><p className="text-sm text-ink-400 mt-0.5">Customers</p></div>
      </div>

      {/* configurable KPI cards for this business */}
      {d.kpis?.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase text-ink-400 mb-2">Key metrics</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {d.kpis.map((k) => (
              <div key={k.name} className="card p-4">
                <p className={`text-2xl font-extrabold tabular-nums ${catColor[k.category] || "text-ink-800"}`}>{num(k.value, k.unit)}</p>
                <p className="text-sm text-ink-500 mt-0.5">{k.name}</p>
                <p className="text-[10px] uppercase text-ink-300">{k.category}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="card p-5 bg-amber-50/50 border-amber-100">
          <p className="text-sm text-ink-600">No KPIs defined for <b>{d.business.name}</b> yet.</p>
          <p className="text-xs text-ink-400 mt-1">Add metrics under <b>Setup → KPI Definitions</b> (pick this business), or connect its API in the Integration Hub. Cards appear here automatically.</p>
        </div>
      )}

      {/* AUM (only for businesses that track it, e.g. FX Artha) */}
      {d.aum && (
        <div>
          <p className="text-xs font-semibold uppercase text-ink-400 mb-2 flex items-center gap-1"><Landmark size={13} /> AUM</p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-4"><p className="text-xl font-extrabold text-emerald-600 tabular-nums">{money(d.aum.new_deposits)}</p><p className="text-xs text-ink-400">New deposits</p></div>
            <div className="card p-4"><p className="text-xl font-extrabold text-rose-500 tabular-nums">{money(d.aum.withdrawals)}</p><p className="text-xs text-ink-400">Withdrawals</p></div>
            <div className="card p-4"><p className={`text-xl font-extrabold tabular-nums ${(d.aum.net_new || 0) < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money(d.aum.net_new)}</p><p className="text-xs text-ink-400">Net New AUM</p></div>
            <div className="card p-4"><p className="text-xl font-extrabold text-ink-800 tabular-nums">{money(d.aum.closing)}</p><p className="text-xs text-ink-400">Closing AUM</p></div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-4">
        {/* revenue trend */}
        <div className="card p-5">
          <p className="text-sm font-bold text-ink-800 flex items-center gap-2 mb-3"><TrendingUp size={16} className="text-brand-600" /> Revenue trend</p>
          {d.revenue_trend?.length ? (
            <div className="space-y-2">
              {d.revenue_trend.map((t) => (
                <div key={t.month} className="flex items-center gap-2">
                  <span className="w-16 text-xs text-ink-400">{t.month}</span>
                  <div className="flex-1 h-4 rounded bg-ink-50 overflow-hidden">
                    <div className="h-full bg-brand-500/70" style={{ width: `${(t.net / maxTrend) * 100}%` }} />
                  </div>
                  <span className="w-20 text-right text-xs font-semibold text-ink-600 tabular-nums">{money(t.net)}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-ink-400">No revenue yet.</p>}
        </div>

        {/* top RMs */}
        <div className="card p-5">
          <p className="text-sm font-bold text-ink-800 mb-3">Top relationship managers</p>
          {d.top_reps?.length ? (
            <div className="space-y-2">
              {d.top_reps.map((r, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="w-5 h-5 grid place-items-center rounded-full bg-ink-100 text-ink-500 text-xs font-bold">{i + 1}</span>
                  <span className="flex-1 text-ink-700 truncate">{r.name}</span>
                  <span className="font-semibold text-emerald-600 tabular-nums">{money(r.revenue)}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-ink-400">No revenue attributed yet.</p>}
        </div>
      </div>
    </div>
  );
}
