import { useEffect, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import {
  Users, UserPlus, Target, CalendarClock, MoreHorizontal, ArrowUpRight,
} from "lucide-react";
import api from "../../api/client";
import { Spinner, Badge } from "../../components/ui";
import { STATUS_COLORS } from "../../config/resources";

const DONUT = ["#6366f1", "#22c55e", "#f59e0b", "#fb7185", "#8b5cf6"];
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
      {trend && (
        <p className="flex items-center gap-1 text-xs font-semibold text-emerald-600 mt-3">
          <ArrowUpRight size={14} /> {trend}
        </p>
      )}
    </div>
  );
}

export default function TeamLeaderDashboard() {
  const [d, setD] = useState(null);

  useEffect(() => {
    api.get("/reports/team-dashboard/").then((r) => setD(r.data)).catch(() => setD(null));
  }, []);

  if (!d) return <Spinner label="Loading your team…" />;

  const statusData = (d.leads_by_status || []).map((s) => ({ name: s.status, count: s.count }));

  return (
    <div className="space-y-5">
      {/* header */}
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Team Dashboard</h1>
        <p className="text-sm text-ink-400 mt-1">Your team's leads, pipeline & performance</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={Users} label="Team Members" value={d.team_size} color="bg-brand-100 text-brand-600" />
        <Kpi icon={UserPlus} label="Team Leads" value={d.team_leads} trend={`${d.team_converted} converted`} color="bg-orange-100 text-orange-600" />
        <Kpi icon={Target} label="Open Deals" value={d.team_open_opportunities} trend={money(d.team_pipeline) + " pipeline"} color="bg-violet-100 text-violet-600" />
        <Kpi icon={CalendarClock} label="Follow-ups" value={d.team_followups} color="bg-rose-100 text-rose-500" />
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        {/* team leads donut */}
        <div className="card p-5 lg:col-span-1">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-ink-900">Team Leads by Status</h3>
            <MoreHorizontal size={18} className="text-ink-300" />
          </div>
          <div className="relative">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={statusData} dataKey="count" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={3}>
                  {statusData.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-3xl font-extrabold text-ink-900 tabular-nums">{d.team_leads}</span>
              <span className="text-xs text-ink-400">Team Leads</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {statusData.map((s, i) => (
              <span key={s.name} className="flex items-center gap-1.5 text-xs text-ink-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT[i % DONUT.length] }} />
                {s.name} ({s.count})
              </span>
            ))}
            {statusData.length === 0 && <span className="text-sm text-ink-400">No leads yet</span>}
          </div>
        </div>

        {/* team performance table */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-bold text-ink-900">Team Performance</h3>
            <MoreHorizontal size={18} className="text-ink-300" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                  <th className="pb-3 pr-4 font-semibold">Name</th>
                  <th className="pb-3 px-4 font-semibold">Role</th>
                  <th className="pb-3 px-4 font-semibold">Leads</th>
                  <th className="pb-3 px-4 font-semibold">Won</th>
                </tr>
              </thead>
              <tbody>
                {(d.members || []).map((m) => (
                  <tr key={m.id} className="border-t border-ink-100 hover:bg-ink-50/70">
                    <td className="py-3.5 pr-4 font-medium text-ink-800">{m.name}</td>
                    <td className="py-3.5 px-4"><Badge value={m.role} map={STATUS_COLORS} /></td>
                    <td className="py-3.5 px-4 text-ink-700 tabular-nums">{m.leads}</td>
                    <td className="py-3.5 px-4 text-ink-700 tabular-nums">{m.won}</td>
                  </tr>
                ))}
                {(!d.members || d.members.length === 0) && (
                  <tr><td colSpan={4} className="py-8 text-center text-ink-400">No team members assigned</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
