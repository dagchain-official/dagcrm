import { Link } from "react-router-dom";
import {
  Boxes, Users, Server, HardDrive, Coins, Activity, RefreshCcw, ArrowRight, Layers,
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

export default function DagChainOverview() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");

  usePolling(() => {
    api.get("/reports/dagchain-overview/")
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load DAGChain overview."));
  }, 6000, []);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading DAGChain…" />;

  const dash = d.dashboard || {};
  const ns = d.node_stats || {};
  const p = d.profiles || {};
  const byKind = Object.fromEntries((d.nodes_by_kind || []).map((k) => [k.kind, k]));
  const val = byKind.validator || {};
  const sto = byKind.storage || {};
  const connected = d.status === "connected";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Boxes className="text-brand-600" /> DAGChain — Overview</h1>
          <p className="text-sm text-ink-400">Platform snapshot · {p.users || 0} users synced into CRM</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${connected ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>{connected ? "Connected" : "Disconnected"}</span>
          <span className="text-xs text-ink-400 inline-flex items-center gap-1"><RefreshCcw size={12} /> {ago(d.last_sync)}</span>
        </div>
      </div>

      {/* headline */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Tile icon={Users} label="Total Users" value={num(dash.totalUsers ?? p.users)} tint="bg-brand-100 text-brand-600" />
        <Tile icon={Coins} label="Node Revenue" value={money(d.node_revenue)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Server} label="Validator Nodes" value={num(val.count)} tint="bg-violet-100 text-violet-600" />
        <Tile icon={HardDrive} label="Storage Nodes" value={num(sto.count)} tint="bg-amber-100 text-amber-600" />
      </div>

      {/* node breakdown */}
      <div className="grid lg:grid-cols-2 gap-5">
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Server size={18} className="text-violet-600" /> Validator Nodes</h3>
          <div className="space-y-3">
            {[["Nodes sold", num(val.count)], ["Revenue", money(val.revenue)],
              ["Blocks validated", num(val.blocks)], ["Rewards earned", num(val.rewards)],
              ["Active now", num(ns.activeValidatorNodes)], ["Blocks today", num(ns.totalBlocksToday)]].map(([l, v]) => (
              <div key={l} className="flex items-center justify-between">
                <span className="text-sm text-ink-500">{l}</span>
                <span className="text-sm font-bold text-ink-900 tabular-nums">{v}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><HardDrive size={18} className="text-amber-600" /> Storage Nodes</h3>
          <div className="space-y-3">
            {[["Nodes sold", num(sto.count)], ["Revenue", money(sto.revenue)],
              ["Rewards earned", num(sto.rewards)], ["Active now", num(ns.activeStorageNodes)],
              ["Rewards paid", num(ns.totalStorageRewardsPaid)], ["Capacity (GB)", num((ns.totalStorageCapacityBytes || 0) / 1073741824)]].map(([l, v]) => (
              <div key={l} className="flex items-center justify-between">
                <span className="text-sm text-ink-500">{l}</span>
                <span className="text-sm font-bold text-ink-900 tabular-nums">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* platform + community */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Tile icon={Activity} label="Transactions" value={num(dash.totalTransactions)} tint="bg-sky-100 text-sky-600" />
        <Tile icon={Layers} label="Total Volume" value={num(dash.totalVolume)} tint="bg-ink-100 text-ink-500" />
        <Tile icon={Coins} label="DGC held (users)" value={num(p.dgc)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Users} label="Referrals" value={num(p.refs)} tint="bg-rose-100 text-rose-500" />
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <Link to="/dagchain-users" className="card p-5 flex items-center justify-between hover:shadow-soft transition">
          <div><p className="font-bold text-ink-900">All Users</p><p className="text-sm text-ink-400">Wallet, DGC balance, referrals, KYC, nodes, RM</p></div>
          <ArrowRight className="text-brand-600" />
        </Link>
        <Link to="/dagchain-nodes" className="card p-5 flex items-center justify-between hover:shadow-soft transition">
          <div><p className="font-bold text-ink-900">All Nodes</p><p className="text-sm text-ink-400">Validator &amp; storage — price, uptime, blocks, rewards, APY</p></div>
          <ArrowRight className="text-brand-600" />
        </Link>
      </div>
    </div>
  );
}
