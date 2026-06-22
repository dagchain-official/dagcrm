import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Users, Target, Trophy, DollarSign, MoreHorizontal, ArrowUpRight,
} from "lucide-react";
import api from "../../api/client";
import { Spinner } from "../../components/ui";

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

function CardHead({ title }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h3 className="font-bold text-ink-900">{title}</h3>
      <MoreHorizontal size={18} className="text-ink-300" />
    </div>
  );
}

export default function SalesManagerDashboard() {
  const [d, setD] = useState(null);

  useEffect(() => {
    api.get("/reports/sales-dashboard/").then((r) => setD(r.data)).catch(() => setD(null));
  }, []);

  if (!d) return <Spinner label="Loading sales dashboard…" />;

  const byStage = d.by_stage || [];
  const leadsBySource = d.leads_by_source || [];
  const topReps = d.top_reps || [];

  return (
    <div className="space-y-5">
      {/* header */}
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Sales Dashboard</h1>
        <p className="text-sm text-ink-400 mt-1">Company-wide sales performance</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={Users} label="Total Leads" value={d.total_leads} trend={`${d.converted_leads} converted`} color="bg-orange-100 text-orange-600" />
        <Kpi icon={Target} label="Open Deals" value={d.open_opportunities} trend={money(d.pipeline_value) + " pipeline"} color="bg-violet-100 text-violet-600" />
        <Kpi icon={Trophy} label="Deals Won" value={d.won_deals} trend={`${d.converted_leads} converted`} color="bg-emerald-100 text-emerald-600" />
        <Kpi icon={DollarSign} label="Net Revenue" value={money(d.net_revenue)} trend={money(d.pipeline_value) + " pipeline"} color="bg-brand-100 text-brand-600" />
      </div>

      {/* charts row */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* bar */}
        <div className="card p-5 lg:col-span-2">
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

        {/* donut */}
        <div className="card p-5 lg:col-span-1">
          <CardHead title="Leads by Source" />
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={leadsBySource} dataKey="count" nameKey="source" innerRadius={55} outerRadius={85} paddingAngle={3}>
                {leadsBySource.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {leadsBySource.map((s, i) => (
              <span key={s.source} className="flex items-center gap-1.5 text-xs text-ink-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT[i % DONUT.length] }} />
                {s.source} ({s.count})
              </span>
            ))}
            {leadsBySource.length === 0 && <span className="text-sm text-ink-400">No leads yet</span>}
          </div>
        </div>
      </div>

      {/* top performers */}
      <div className="card p-5">
        <CardHead title="Top Performers" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 pr-4 font-semibold">S/N</th>
                <th className="pb-3 px-4 font-semibold">Name</th>
                <th className="pb-3 px-4 font-semibold">Leads</th>
                <th className="pb-3 px-4 font-semibold">Deals Won</th>
              </tr>
            </thead>
            <tbody>
              {topReps.map((r, i) => (
                <tr key={i} className="border-t border-ink-100 hover:bg-ink-50/70">
                  <td className="py-3.5 pr-4 text-ink-400">{String(i + 1).padStart(2, "0")}</td>
                  <td className="py-3.5 px-4 font-medium text-ink-800">{r.name}</td>
                  <td className="py-3.5 px-4 text-ink-700 tabular-nums">{r.leads}</td>
                  <td className="py-3.5 px-4 font-semibold text-ink-900 tabular-nums">{r.won}</td>
                </tr>
              ))}
              {topReps.length === 0 && (
                <tr><td colSpan={4} className="py-8 text-center text-ink-400">No performers yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
