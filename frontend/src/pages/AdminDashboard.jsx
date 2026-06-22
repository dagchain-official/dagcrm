import { useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Users, UserCheck, Target, LifeBuoy, MoreHorizontal, ArrowUpRight,
  Sparkles, TrendingUp,
} from "lucide-react";
import api, { ai } from "../api/client";
import { Badge, Spinner } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const DONUT = ["#f97316", "#fb7185", "#8b5cf6", "#6366f1", "#22c55e", "#06b6d4"];
const money = (v) => `$${Number(v || 0).toLocaleString()}`;

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
      <p className="flex items-center gap-1 text-xs font-semibold text-emerald-600 mt-3">
        <ArrowUpRight size={14} /> {trend}
      </p>
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

export default function AdminDashboard() {
  const [kpi, setKpi] = useState(null);
  const [byStage, setByStage] = useState([]);
  const [byStatus, setByStatus] = useState([]);
  const [trend, setTrend] = useState([]);
  const [revenue, setRevenue] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    Promise.all([
      api.get("/reports/dashboard/"),
      api.get("/reports/opportunities-by-stage/"),
      api.get("/reports/leads-by-status/"),
      api.get("/reports/revenue-trend/"),
      api.get("/revenues/?page_size=5"),
      api.get("/tickets/?page_size=5"),
    ]).then(([d, s, st, tr, rev, tk]) => {
      setKpi(d.data);
      setByStage(s.data);
      setByStatus(st.data);
      setTrend(tr.data);
      setRevenue(rev.data.results || rev.data);
      setTickets(tk.data.results || tk.data);
      ai.post("/insights/summary", d.data).then((r) => setInsights(r.data.insights)).catch(() => {});
    });
  }, []);

  if (!kpi) return <Spinner label="Loading dashboard…" />;

  const totalLeads = kpi.total_leads || 0;
  const sevTint = { good: "bg-emerald-50 text-emerald-700", warning: "bg-amber-50 text-amber-700", info: "bg-blue-50 text-blue-700" };
  const stat = (s) => byStatus.find((x) => x.status === s)?.count || 0;

  return (
    <div className="space-y-5">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={Users} label="Total Leads" value={totalLeads} trend={`${kpi.new_leads} new this period`} color="bg-orange-100 text-orange-600" />
        <Kpi icon={UserCheck} label="Total Customers" value={kpi.total_customers} trend={`${kpi.converted_leads} converted`} color="bg-rose-100 text-rose-500" />
        <Kpi icon={Target} label="Open Opportunities" value={kpi.open_opportunities} trend={money(kpi.pipeline_value) + " pipeline"} color="bg-violet-100 text-violet-600" />
        <Kpi icon={LifeBuoy} label="Open Tickets" value={kpi.open_tickets} trend="support queue" color="bg-blue-100 text-blue-600" />
      </div>

      {/* charts row */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* donut */}
        <div className="card p-5">
          <CardHead title="Leads Overview" />
          <div className="relative">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={byStatus} dataKey="count" nameKey="status" innerRadius={62} outerRadius={88} paddingAngle={3}>
                  {byStatus.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-3xl font-extrabold text-ink-900 tabular-nums">{totalLeads}</span>
              <span className="text-xs text-ink-400">Total Leads</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-5 pt-4 border-t border-ink-100">
            {[["New", stat("new"), "text-blue-600"], ["Converted", stat("converted"), "text-emerald-600"], ["Lost", stat("lost"), "text-rose-500"]].map(([l, v, c]) => (
              <div key={l} className="text-center">
                <p className={`text-xl font-extrabold ${c} tabular-nums`}>{v}</p>
                <p className="text-[11px] text-ink-400 mt-0.5">{l}</p>
              </div>
            ))}
          </div>
        </div>

        {/* bar */}
        <div className="card p-5">
          <CardHead title="Opportunities by Stage" />
          <ResponsiveContainer width="100%" height={245}>
            <BarChart data={byStage} barSize={26}>
              <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="stage" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: "#f8fafc" }} />
              <Bar dataKey="count" radius={[8, 8, 8, 8]} fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* total income area */}
        <div className="card p-5">
          <CardHead title="Total Revenue" />
          <p className="text-3xl font-extrabold text-ink-900 tabular-nums">{money(kpi.net_revenue)}</p>
          <p className="flex items-center gap-1 text-xs font-semibold text-emerald-600 mt-1">
            <TrendingUp size={14} /> Gross {money(kpi.gross_revenue)}
          </p>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={trend} margin={{ top: 16, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip />
              <Area type="monotone" dataKey="net" stroke="#6366f1" strokeWidth={2.5} fill="url(#g)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* tables + AI row */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* recent revenue */}
        <div className="card p-5 lg:col-span-2">
          <CardHead title="Recent Revenue" />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                  <th className="pb-3 font-semibold">S/N</th>
                  <th className="pb-3 font-semibold">Customer</th>
                  <th className="pb-3 font-semibold">Business</th>
                  <th className="pb-3 font-semibold text-right">Net</th>
                </tr>
              </thead>
              <tbody>
                {revenue.map((r, i) => (
                  <tr key={r.id} className="border-t border-ink-100">
                    <td className="py-3 text-ink-400">{String(i + 1).padStart(2, "0")}</td>
                    <td className="py-3 font-medium text-ink-800">{r.customer_name || "—"}</td>
                    <td className="py-3 text-ink-500">{r.business_name || "—"}</td>
                    <td className="py-3 text-right font-semibold text-ink-900 tabular-nums">{money(r.net_revenue)}</td>
                  </tr>
                ))}
                {revenue.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-ink-400">No revenue yet</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI insights */}
        <div className="card p-5">
          <CardHead title="AI Insights" action={<Sparkles size={18} className="text-brand-500" />} />
          <div className="space-y-3">
            {insights.length === 0 && <p className="text-sm text-ink-400">Crunching numbers…</p>}
            {insights.map((it, i) => (
              <div key={i} className="p-3 rounded-2xl bg-ink-50 border border-ink-100">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-ink-800">{it.title}</p>
                  <span className={`badge ${sevTint[it.severity] || sevTint.info}`}>{it.severity}</span>
                </div>
                <p className="text-xs text-ink-500 mt-1">{it.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* recent tickets */}
      <div className="card p-5">
        <CardHead title="Recent Support Tickets" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 font-semibold">Ticket</th>
                <th className="pb-3 font-semibold">Customer</th>
                <th className="pb-3 font-semibold">Category</th>
                <th className="pb-3 font-semibold">Priority</th>
                <th className="pb-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} className="border-t border-ink-100">
                  <td className="py-3 font-medium text-ink-800">{t.ticket_no}</td>
                  <td className="py-3 text-ink-500">{t.customer_name || "—"}</td>
                  <td className="py-3 text-ink-500">{t.category || "—"}</td>
                  <td className="py-3"><Badge value={t.priority} map={STATUS_COLORS} /></td>
                  <td className="py-3"><Badge value={t.status} map={STATUS_COLORS} /></td>
                </tr>
              ))}
              {tickets.length === 0 && <tr><td colSpan={5} className="py-6 text-center text-ink-400">No tickets</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
