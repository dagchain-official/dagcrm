import { useState } from "react";
import {
  Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  DollarSign, TrendingUp, Receipt, Handshake, MoreHorizontal, ArrowUpRight,
} from "lucide-react";
import api from "../../api/client";
import usePolling from "../../hooks/usePolling";
import { Spinner } from "../../components/ui";

const PIE_COLORS = ["#6366f1", "#f59e0b", "#22c55e", "#fb7185", "#8b5cf6", "#06b6d4"];
const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const pct = (v) => `${(Number(v || 0) * 100).toFixed(2)}%`;
const BAND = { Healthy: "bg-emerald-50 text-emerald-700", Watch: "bg-amber-50 text-amber-700", Critical: "bg-rose-50 text-rose-600" };

function Kpi({ icon: Icon, label, value, trend, color }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div className={`grid place-items-center w-11 h-11 rounded-2xl ${color}`}>
          <Icon size={20} />
        </div>
        <MoreHorizontal size={18} className="text-ink-300" />
      </div>
      <p className="text-3xl font-extrabold text-ink-900 mt-4 tabular-nums">{value}</p>
      <p className="text-sm text-ink-400 mt-0.5">{label}</p>
      {trend && (
        <p className="flex items-center gap-1 text-xs font-semibold text-emerald-600 mt-3">
          <ArrowUpRight size={14} /> {trend}
        </p>
      )}
    </div>
  );
}

export default function FinanceDashboard() {
  const [d, setD] = useState(null);

  usePolling(() => {
    api.get("/reports/finance-dashboard/").then((r) => setD(r.data)).catch(() => {});
  });

  if (!d) return <Spinner label="Loading finance dashboard…" />;

  const revenueByBusiness = d.revenue_by_business || [];
  const expensesByType = d.expenses_by_type || [];
  const pnl = d.pnl || [];

  return (
    <div className="space-y-5">
      {/* header */}
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Finance Dashboard</h1>
        <p className="text-sm text-ink-400 mt-0.5">Revenue, expenses, commissions &amp; profit</p>
      </div>

      {/* profit highlight */}
      <div className="card p-6 bg-gradient-to-r from-brand-600 to-brand-500 text-white border-0">
        <p className="text-sm text-white/80">Net Profit</p>
        <p className="text-4xl font-extrabold mt-1 tabular-nums">{money(d.profit)}</p>
        <p className="text-sm text-white/80 mt-2">
          Net revenue {money(d.net_revenue)} − expenses {money(d.total_expenses)} − commissions{" "}
          {money(d.total_commissions)} − payroll {money(d.payroll_this_month)}
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={DollarSign} label="Gross Revenue" value={money(d.gross_revenue)} color="bg-emerald-100 text-emerald-600" />
        <Kpi icon={TrendingUp} label="Net Revenue" value={money(d.net_revenue)} color="bg-brand-100 text-brand-600" />
        <Kpi icon={Receipt} label="Expenses" value={money(d.total_expenses)} color="bg-rose-100 text-rose-500" />
        <Kpi icon={Handshake} label="Commissions" value={money(d.total_commissions)} color="bg-amber-100 text-amber-600" />
      </div>

      {/* P&L — revenue, collection, cost and profit health (data-driven) */}
      {pnl.length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4">P&amp;L — Profit Health</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm max-w-2xl">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide border-b border-ink-100">
                  <th className="py-2 pr-4 font-semibold">Metric</th>
                  <th className="py-2 px-4 font-semibold text-right">Amount / Rate</th>
                  <th className="py-2 pl-4 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {pnl.map((row) => (
                  <tr key={row.metric} className="border-b border-ink-50">
                    <td className="py-2.5 pr-4 font-medium text-ink-800">{row.metric}</td>
                    <td className="py-2.5 px-4 text-right tabular-nums text-ink-900">
                      {row.rate ? pct(row.amount) : money(row.amount)}
                    </td>
                    <td className="py-2.5 pl-4 text-right">
                      <span className={`badge ${BAND[row.status] || "bg-ink-100 text-ink-500"}`}>{row.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* charts */}
      <div className="grid lg:grid-cols-2 gap-5">
        {/* revenue by business */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-ink-900">Revenue by Business</h3>
            <MoreHorizontal size={18} className="text-ink-300" />
          </div>
          {revenueByBusiness.length === 0 ? (
            <p className="text-sm text-ink-400 py-16 text-center">No revenue data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={revenueByBusiness} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="business" type="category" width={90} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => money(v)} />
                <Bar dataKey="net" fill="#6366f1" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* expenses by type */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-ink-900">Expenses by Type</h3>
            <MoreHorizontal size={18} className="text-ink-300" />
          </div>
          {expensesByType.length === 0 ? (
            <p className="text-sm text-ink-400 py-16 text-center">No expenses recorded yet</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={expensesByType} dataKey="total" nameKey="expense_type" innerRadius={64} outerRadius={96} paddingAngle={3}>
                    {expensesByType.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => money(v)} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-2 mt-4 justify-center">
                {expensesByType.map((e, i) => (
                  <span key={e.expense_type} className="flex items-center gap-1.5 text-xs text-ink-500">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                    {e.expense_type} ({money(e.total)})
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
