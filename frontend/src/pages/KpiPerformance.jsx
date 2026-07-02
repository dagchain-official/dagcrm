import { useState, useEffect } from "react";
import { Activity, Zap } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const now = new Date();
const catColor = { growth: "bg-emerald-50 text-emerald-700", activity: "bg-blue-50 text-blue-700", other: "bg-ink-100 text-ink-600" };
const fmt = (v, u) => (u === "$" ? `$${Number(v || 0).toLocaleString()}` : u && u !== "count" ? `${v} ${u}` : v);

export default function KpiPerformance() {
  const [rows, setRows] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [metric, setMetric] = useState("");
  const [employee, setEmployee] = useState("");

  useEffect(() => {
    api.get("/metric-definitions/?page_size=200").then((r) => setMetrics(r.data.results || r.data)).catch(() => {});
    api.get("/employees/?page_size=200").then((r) => setEmployees(r.data.results || r.data)).catch(() => {});
  }, []);

  usePolling(() => {
    api.get("/reports/kpi-performance/", { params: { month, year, metric: metric || undefined, employee: employee || undefined } })
      .then((r) => setRows(r.data.rows)).catch(() => setRows([]));
  }, 4000, [month, year, metric, employee]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink-900 flex items-center gap-2"><Zap size={18} className="text-brand-600" /> Auto Performance</h2>
          <p className="text-xs text-ink-400">KPI values auto-detected from CRM activity — filter any way you like.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select className="input !w-auto" value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="">All metrics</option>
            {metrics.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <select className="input !w-auto" value={employee} onChange={(e) => setEmployee(e.target.value)}>
            <option value="">All employees</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.user_name}</option>)}
          </select>
          <select className="input !w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select className="input !w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {rows === null ? <Spinner label="Detecting…" /> : rows.length === 0 ? (
        <EmptyState title="No activity detected" hint="No KPI activity for this filter. Try another month/metric/employee." />
      ) : (
        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide border-b border-ink-100">
                <th className="px-4 py-3 font-semibold">Employee</th>
                <th className="px-4 py-3 font-semibold">Metric</th>
                <th className="px-4 py-3 font-semibold text-right">Value</th>
                <th className="px-4 py-3 font-semibold">Category</th>
                <th className="px-4 py-3 font-semibold">Source</th>
                <th className="px-4 py-3 font-semibold">Period</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-ink-50 hover:bg-ink-50/60">
                  <td className="px-4 py-2.5 font-medium text-ink-800">{r.employee}</td>
                  <td className="px-4 py-2.5 text-ink-600">{r.metric}</td>
                  <td className="px-4 py-2.5 text-right font-bold text-ink-900 tabular-nums">{fmt(r.value, r.unit)}</td>
                  <td className="px-4 py-2.5"><span className={`badge ${catColor[r.category] || ""}`}>{r.category}</span></td>
                  <td className="px-4 py-2.5">
                    <span className={`badge ${r.source === "derived" ? "bg-violet-50 text-violet-700" : "bg-ink-100 text-ink-600"}`}>
                      {r.source === "derived" ? "auto" : "manual"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-ink-500">{String(r.month).padStart(2, "0")}/{r.year}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
