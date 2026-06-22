import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import api from "../api/client";
import { Spinner } from "../components/ui";

export default function Reports() {
  const [status, setStatus] = useState([]);
  const [biz, setBiz] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/reports/leads-by-status/"),
      api.get("/reports/revenue-by-business/"),
    ])
      .then(([s, b]) => {
        setStatus(s.data);
        setBiz(b.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">Reports</h1>
        <p className="text-sm text-ink-400">Sales, revenue & pipeline analytics</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4">Leads by Status</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={status}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef0f4" vertical={false} />
              <XAxis dataKey="status" tick={{ fontSize: 12, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} />
              <Tooltip />
              <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="#22c55e" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4">Revenue by Business</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={biz} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef0f4" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#94a3b8" }} />
              <YAxis type="category" dataKey="business" width={90} tick={{ fontSize: 12, fill: "#94a3b8" }} />
              <Tooltip />
              <Bar dataKey="gross" radius={[0, 8, 8, 0]} fill="#6366f1" name="Gross" />
              <Bar dataKey="net" radius={[0, 8, 8, 0]} fill="#a5b4fc" name="Net" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-4">Revenue Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <th className="pb-3 px-4 font-semibold">Business</th>
                <th className="pb-3 px-4 font-semibold text-right">Gross</th>
                <th className="pb-3 px-4 font-semibold text-right">Net</th>
              </tr>
            </thead>
            <tbody>
              {biz.map((b) => (
                <tr key={b.business} className="border-t border-ink-100 hover:bg-ink-50/70">
                  <td className="px-4 py-3 font-medium text-ink-700">{b.business}</td>
                  <td className="px-4 py-3 text-right tabular-nums">${Number(b.gross).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right tabular-nums">${Number(b.net).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
