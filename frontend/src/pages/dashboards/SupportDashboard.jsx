import { useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import {
  LifeBuoy, Inbox, CheckCircle2, AlertTriangle, MoreHorizontal, ArrowUpRight,
} from "lucide-react";
import api from "../../api/client";
import usePolling from "../../hooks/usePolling";
import { Spinner, Badge } from "../../components/ui";
import { STATUS_COLORS } from "../../config/resources";

const PRIORITY_COLORS = { urgent: "#ef4444", high: "#f59e0b", medium: "#6366f1", low: "#94a3b8" };
const FALLBACK = ["#6366f1", "#22c55e", "#f59e0b", "#fb7185", "#8b5cf6", "#06b6d4"];

function Kpi({ icon: Icon, label, value, color }) {
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

export default function SupportDashboard() {
  const [d, setD] = useState(null);

  usePolling(() => {
    api.get("/reports/support-dashboard/").then((r) => setD(r.data)).catch(() => {});
  });

  if (!d) return <Spinner label="Loading support dashboard…" />;

  const byStatus = d.by_status || [];
  const byPriority = d.by_priority || [];

  return (
    <div className="space-y-5">
      {/* header */}
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Support Dashboard</h1>
        <p className="text-sm text-ink-400 mt-1">Ticket queue health &amp; priorities</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={LifeBuoy} label="Total Tickets" value={d.total_tickets} color="bg-brand-100 text-brand-600" />
        <Kpi icon={Inbox} label="Open Tickets" value={d.open_tickets} color="bg-amber-100 text-amber-600" />
        <Kpi icon={CheckCircle2} label="Resolved" value={d.resolved_tickets} color="bg-emerald-100 text-emerald-600" />
        <Kpi icon={AlertTriangle} label="Urgent Open" value={d.urgent_tickets} color="bg-rose-100 text-rose-500" />
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* tickets by status */}
        <div className="card p-5">
          <CardHead title="Tickets by Status" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byStatus}>
              <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="status" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#94a3b8" }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#94a3b8" }} allowDecimals={false} />
              <Tooltip cursor={{ fill: "#f8fafc" }} />
              <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 8, 8]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* tickets by priority */}
        <div className="card p-5">
          <CardHead title="Tickets by Priority" />
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={byPriority} dataKey="count" nameKey="priority" innerRadius={60} outerRadius={88} paddingAngle={3}>
                {byPriority.map((p, i) => (
                  <Cell key={i} fill={PRIORITY_COLORS[p.priority] || FALLBACK[i % FALLBACK.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {byPriority.map((p) => (
              <span key={p.priority} className="flex items-center gap-1.5 text-xs text-ink-500">
                <Badge value={p.priority} map={STATUS_COLORS} /> ({p.count})
              </span>
            ))}
            {byPriority.length === 0 && <span className="text-sm text-ink-400">No tickets yet</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
