import { Link } from "react-router-dom";
import {
  LineChart, Users, CandlestickChart, ArrowDownToLine, ArrowUpFromLine,
  DollarSign, Activity, RefreshCcw, ArrowRight,
} from "lucide-react";
import { useState } from "react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
const ago = (v) => {
  if (!v) return "never";
  const s = Math.floor((Date.now() - new Date(v)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

function Tile({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-11 h-11 rounded-2xl ${tint}`}><Icon size={20} /></div>
      <p className="text-2xl font-extrabold text-ink-900 mt-4 tabular-nums">{value}</p>
      <p className="text-sm text-ink-400 mt-0.5">{label}</p>
    </div>
  );
}

export default function FxArthaOverview() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");

  usePolling(() => {
    api.get("/reports/fxartha-overview/")
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load FX Artha overview."));
  }, 6000, []);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading FX Artha…" />;

  const dash = d.dashboard || {};
  const connected = d.status === "connected";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><LineChart className="text-brand-600" /> FX Artha — Overview</h1>
          <p className="text-sm text-ink-400">Platform snapshot (last sync) · {d.synced_traders} traders in CRM</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${connected ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>{connected ? "Connected" : "Disconnected"}</span>
          <span className="text-xs text-ink-400 inline-flex items-center gap-1"><RefreshCcw size={12} /> {ago(d.last_sync)}</span>
        </div>
      </div>

      {Object.keys(dash).length === 0 ? (
        <div className="card p-10 text-center">
          <p className="text-ink-500 font-semibold">Abhi koi snapshot nahi.</p>
          <p className="text-sm text-ink-400 mt-1">Integration Hub → FX Artha me valid API key daal ke <b>Sync now</b> dabao.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
          <Tile icon={Users} label="Total Traders" value={num(dash.total_traders)} tint="bg-brand-100 text-brand-600" />
          <Tile icon={Activity} label="Active Accounts" value={num(dash.active_accounts)} tint="bg-emerald-100 text-emerald-600" />
          <Tile icon={CandlestickChart} label="Lots Traded" value={num(dash.lots_traded)} tint="bg-violet-100 text-violet-600" />
          <Tile icon={ArrowDownToLine} label="Total Deposits" value={money(dash.total_deposits)} tint="bg-sky-100 text-sky-600" />
          <Tile icon={ArrowUpFromLine} label="Total Withdrawals" value={money(dash.total_withdrawals)} tint="bg-rose-100 text-rose-500" />
          <Tile icon={DollarSign} label="Monthly Revenue" value={money(dash.monthly_revenue)} tint="bg-amber-100 text-amber-600" />
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        <Link to="/fxartha-traders" className="card p-5 flex items-center justify-between hover:shadow-soft transition">
          <div><p className="font-bold text-ink-900">All Traders</p><p className="text-sm text-ink-400">Har trader ki poori detail — lots, brokerage, deposits, RM</p></div>
          <ArrowRight className="text-brand-600" />
        </Link>
        <Link to="/traders-lots" className="card p-5 flex items-center justify-between hover:shadow-soft transition">
          <div><p className="font-bold text-ink-900">Lots &amp; Commission</p><p className="text-sm text-ink-400">Employee-wise lots × rate = commission</p></div>
          <ArrowRight className="text-brand-600" />
        </Link>
      </div>
    </div>
  );
}
