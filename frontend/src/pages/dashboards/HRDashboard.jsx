import { useState } from "react";
import {
  Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Users, UserCheck, CalendarOff, Wallet, MoreHorizontal, ArrowUpRight,
} from "lucide-react";
import api from "../../api/client";
import usePolling from "../../hooks/usePolling";
import { Spinner } from "../../components/ui";

const PIE_COLORS = ["#f59e0b", "#22c55e", "#ef4444"];
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

export default function HRDashboard() {
  const [d, setD] = useState(null);

  usePolling(() => {
    api.get("/reports/hr-dashboard/").then((r) => setD(r.data)).catch(() => {});
  });

  if (!d) return <Spinner label="Loading HR dashboard…" />;

  const deptData = (d.headcount_by_dept || []).map((x) => ({
    department__department_name: x.department__department_name || "Unassigned",
    count: x.count,
  }));
  const leaveData = (d.leaves_by_status || []).map((x) => ({ status: x.status, count: x.count }));

  return (
    <div className="space-y-5">
      {/* header */}
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">HR Dashboard</h1>
        <p className="text-sm text-ink-400">People, attendance, leaves &amp; payroll</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={Users} label="Total Employees" value={d.total_employees} trend={`${d.on_leave_today} on leave today`} color="bg-brand-100 text-brand-600" />
        <Kpi icon={UserCheck} label="Present Today" value={d.present_today} trend={`${d.total_employees} total staff`} color="bg-emerald-100 text-emerald-600" />
        <Kpi icon={CalendarOff} label="Pending Leaves" value={d.pending_leaves} trend={`${d.on_leave_today} on leave today`} color="bg-amber-100 text-amber-600" />
        <Kpi icon={Wallet} label="Payroll This Month" value={money(d.payroll_this_month)} trend={`${money(d.incentives_this_month)} incentives`} color="bg-violet-100 text-violet-600" />
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* headcount by department */}
        <div className="card p-5">
          <CardHead title="Headcount by Department" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={deptData}>
              <XAxis dataKey="department__department_name" tick={{ fontSize: 12, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip cursor={{ fill: "#f1f5f9" }} />
              <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
          {deptData.length === 0 && <p className="text-sm text-ink-400 text-center py-4">No department data yet</p>}
        </div>

        {/* leaves by status */}
        <div className="card p-5">
          <CardHead title="Leaves by Status" />
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={leaveData} dataKey="count" nameKey="status" innerRadius={64} outerRadius={92} paddingAngle={3}>
                {leaveData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {leaveData.map((s, i) => (
              <span key={s.status} className="flex items-center gap-1.5 text-xs text-ink-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                {s.status} ({s.count})
              </span>
            ))}
            {leaveData.length === 0 && <span className="text-sm text-ink-400">No leave data yet</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
