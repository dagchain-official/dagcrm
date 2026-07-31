import { useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Users, Trophy, DollarSign, TrendingUp, Layers, AlertTriangle, GraduationCap, ClipboardCheck,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const num = (v) => Number(v || 0).toLocaleString();
const pct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`;

const BAND = {
  Healthy: { bar: "#22c55e", chip: "bg-emerald-50 text-emerald-700" },
  Watch: { bar: "#f59e0b", chip: "bg-amber-50 text-amber-700" },
  Critical: { bar: "#ef4444", chip: "bg-rose-50 text-rose-600" },
};

function Tile({ icon: Icon, label, value, color }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-11 h-11 rounded-2xl ${color}`}><Icon size={20} /></div>
      <p className="text-3xl font-extrabold text-ink-900 mt-4 tabular-nums">{value}</p>
      <p className="text-sm text-ink-400 mt-0.5">{label}</p>
    </div>
  );
}

export default function AdminDashboard() {
  const [d, setD] = useState(null);

  usePolling(() => {
    api.get("/reports/company-health/").then((r) => setD(r.data)).catch(() => {});
  });

  if (!d) return <Spinner label="Loading company health…" />;

  const health = d.health || [];
  const dims = health.filter((h) => h.dimension !== "Overall");
  const overall = health.find((h) => h.dimension === "Overall") || {};
  const chartData = health.map((h) => ({ name: h.dimension, score: h.score, status: h.status }));

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">CEO Command Center</h1>
        <p className="text-sm text-ink-400 mt-1">Company health, growth, execution and risk in one view.</p>
      </div>

      {/* headline numbers */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Tile icon={Users} label="Active Leads" value={num(d.total_leads)} color="bg-orange-100 text-orange-600" />
        <Tile icon={Trophy} label="Closed Won" value={num(d.closed_won)} color="bg-emerald-100 text-emerald-600" />
        <Tile icon={DollarSign} label="Revenue" value={money(d.revenue)} color="bg-brand-100 text-brand-600" />
        <Tile icon={TrendingUp} label="Gross Profit" value={money(d.gross_profit)} color="bg-teal-100 text-teal-600" />
        <Tile icon={Layers} label="Weighted Pipeline" value={money(d.weighted_pipeline)} color="bg-violet-100 text-violet-600" />
        <Tile icon={AlertTriangle} label="Overdue Actions" value={num(d.overdue_actions)} color="bg-rose-100 text-rose-500" />
        <Tile icon={GraduationCap} label="Training Compliance" value={pct(d.training_compliance)} color="bg-indigo-100 text-indigo-600" />
        <Tile icon={ClipboardCheck} label="Assessment Pass Rate" value={pct(d.assessment_pass_rate)} color="bg-sky-100 text-sky-600" />
      </div>

      {/* company health — table + chart */}
      <div className="grid lg:grid-cols-3 gap-5">
        <div className="card p-5 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-ink-900">Company Health</h3>
            <span className={`badge ${BAND[overall.status]?.chip || ""}`}>{overall.status}</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide border-b border-ink-100">
                <th className="py-2 pr-3 font-semibold">Dimension</th>
                <th className="py-2 px-3 font-semibold text-right">Score</th>
                <th className="py-2 pl-3 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              {dims.map((h) => (
                <tr key={h.dimension} className="border-b border-ink-50">
                  <td className="py-2 pr-3 font-medium text-ink-800">{h.dimension}</td>
                  <td className="py-2 px-3 text-right tabular-nums text-ink-700">{pct(h.score)}</td>
                  <td className="py-2 pl-3 text-right"><span className={`badge ${BAND[h.status]?.chip || ""}`}>{h.status}</span></td>
                </tr>
              ))}
              <tr className="border-t-2 border-ink-200 font-bold">
                <td className="py-2.5 pr-3 text-ink-900">Overall</td>
                <td className="py-2.5 px-3 text-right tabular-nums text-ink-900">{pct(overall.score)}</td>
                <td className="py-2.5 pl-3 text-right"><span className={`badge ${BAND[overall.status]?.chip || ""}`}>{overall.status}</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="card p-5 lg:col-span-2">
          <h3 className="font-bold text-ink-900 mb-4">Company Health</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} barSize={44}>
              <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: "#f8fafc" }} formatter={(v) => pct(v)} />
              <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                {chartData.map((c, i) => <Cell key={i} fill={BAND[c.status]?.bar || "#6366f1"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <p className="text-xs text-ink-400">
        <b>Note:</b> Training Compliance, Assessment Pass Rate and the Learning dimension read 0 until a
        Training / Assessment module is added. Every other number is live.
      </p>
    </div>
  );
}
