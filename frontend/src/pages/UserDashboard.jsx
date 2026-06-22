import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import {
  UserPlus, Target, TrendingUp, CalendarClock, MoreHorizontal, ArrowUpRight,
  Trophy, Activity, ChevronRight, DollarSign,
} from "lucide-react";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Badge, ScorePill, Spinner } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const DONUT = ["#6366f1", "#22c55e", "#f59e0b", "#fb7185", "#8b5cf6", "#06b6d4"];
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

function CardHead({ title, to }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h3 className="font-bold text-ink-900">{title}</h3>
      {to ? (
        <Link to={to} className="text-xs font-semibold text-brand-600 flex items-center gap-0.5">
          View all <ChevronRight size={14} />
        </Link>
      ) : (
        <MoreHorizontal size={18} className="text-ink-300" />
      )}
    </div>
  );
}

export default function UserDashboard() {
  const { user } = useAuth();
  const [d, setD] = useState(null);

  useEffect(() => {
    api.get("/reports/my-dashboard/").then((r) => setD(r.data)).catch(() => setD(null));
  }, []);

  if (!d) return <Spinner label="Loading your workspace…" />;

  const statusData = (d.leads_by_status || []).map((s) => ({ name: s.status, count: s.count }));

  return (
    <div className="space-y-5">
      {/* greeting banner */}
      <div className="card p-6 bg-gradient-to-r from-brand-600 to-brand-500 text-white border-0 relative overflow-hidden">
        <div className="absolute -top-10 -right-6 w-48 h-48 rounded-full bg-white/10" />
        <div className="relative">
          <p className="text-sm text-white/80">My Workspace</p>
          <h1 className="text-2xl font-extrabold mt-1">Hi {user?.name?.split(" ")[0]}, here's your day 👋</h1>
          <p className="text-sm text-white/80 mt-1">
            You have <b>{d.my_followups_due}</b> follow-up{d.my_followups_due !== 1 ? "s" : ""} coming up and{" "}
            <b>{d.my_open_opportunities}</b> open deal{d.my_open_opportunities !== 1 ? "s" : ""}.
          </p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={UserPlus} label="My Leads" value={d.my_leads} trend={`${d.my_new_leads} new`} color="bg-orange-100 text-orange-600" />
        <Kpi icon={DollarSign} label="My Revenue" value={money(d.my_revenue)} trend={`${d.my_won} deals won`} color="bg-emerald-100 text-emerald-600" />
        <Kpi icon={Target} label="My Open Deals" value={d.my_open_opportunities} trend={money(d.my_pipeline_value) + " pipeline"} color="bg-violet-100 text-violet-600" />
        <Kpi icon={CalendarClock} label="Follow-ups Due" value={d.my_followups_due} trend={`${d.my_activities_today} done today`} color="bg-rose-100 text-rose-500" />
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        {/* my leads donut */}
        <div className="card p-5">
          <CardHead title="My Leads by Status" to="/m/leads" />
          <div className="relative">
            <ResponsiveContainer width="100%" height={190}>
              <PieChart>
                <Pie data={statusData} dataKey="count" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={3}>
                  {statusData.map((_, i) => <Cell key={i} fill={DONUT[i % DONUT.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-3xl font-extrabold text-ink-900 tabular-nums">{d.my_leads}</span>
              <span className="text-xs text-ink-400">My Leads</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {statusData.map((s, i) => (
              <span key={s.name} className="flex items-center gap-1.5 text-xs text-ink-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT[i % DONUT.length] }} />
                {s.name} ({s.count})
              </span>
            ))}
            {statusData.length === 0 && <span className="text-sm text-ink-400">No leads assigned yet</span>}
          </div>
        </div>

        {/* upcoming follow-ups */}
        <div className="card p-5 lg:col-span-2">
          <CardHead title="Upcoming Follow-ups" to="/m/lead-activities" />
          <div className="space-y-2">
            {(d.upcoming_followups || []).map((f) => (
              <div key={f.id} className="flex items-center gap-3 p-3 rounded-2xl bg-ink-50 border border-ink-100">
                <div className="grid place-items-center w-9 h-9 rounded-xl bg-brand-100 text-brand-600 shrink-0">
                  <Activity size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-ink-800 truncate">{f.lead__name || "Lead"}</p>
                  <p className="text-xs text-ink-400 truncate">{f.next_action || f.activity_type}</p>
                </div>
                <span className="badge bg-amber-50 text-amber-700 shrink-0">{f.followup_date}</span>
              </div>
            ))}
            {(!d.upcoming_followups || d.upcoming_followups.length === 0) && (
              <p className="text-sm text-ink-400 py-8 text-center">No upcoming follow-ups. 🎉</p>
            )}
          </div>
        </div>
      </div>

      {/* recent leads */}
      <div className="card p-5">
        <CardHead title="My Recent Leads" to="/m/leads" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 pr-4 font-semibold">Code</th>
                <th className="pb-3 px-4 font-semibold">Name</th>
                <th className="pb-3 px-4 font-semibold">Score</th>
                <th className="pb-3 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {(d.recent_leads || []).map((l) => (
                <tr key={l.id} className="border-t border-ink-100 hover:bg-ink-50/70">
                  <td className="py-3.5 pr-4 font-medium text-ink-800">{l.lead_code}</td>
                  <td className="py-3.5 px-4 text-ink-700">{l.name}</td>
                  <td className="py-3.5 px-4"><ScorePill value={l.score} /></td>
                  <td className="py-3.5 px-4"><Badge value={l.status} map={STATUS_COLORS} /></td>
                </tr>
              ))}
              {(!d.recent_leads || d.recent_leads.length === 0) && (
                <tr><td colSpan={4} className="py-8 text-center text-ink-400">No leads assigned to you yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
