import { Link } from "react-router-dom";
import {
  Boxes, Users, Server, HardDrive, Coins, Activity, RefreshCcw, ArrowRight, Layers,
  Lock, ExternalLink, Package, Percent,
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
  const st = d.staking || {};                 // contract-level staking
  const nst = d.node_staking || {};           // per-node staking (separate)
  const tranches = st.tranches || [];
  const prods = d.products || {};
  const validators = prods.validators || [];
  const storage = prods.storage || [];
  const aprRates = prods.apr_rates || [];
  const shortAddr = (a) => (a ? `${a.slice(0, 6)}…${a.slice(-4)}` : "—");
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
      <div data-tour="dc-tiles" className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Tile icon={Users} label="Total Users" value={num(dash.totalUsers ?? p.users)} tint="bg-brand-100 text-brand-600" />
        <Tile icon={Coins} label="Node Revenue" value={money(d.node_revenue)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Server} label="Validator Nodes" value={num(val.count)} tint="bg-violet-100 text-violet-600" />
        <Tile icon={HardDrive} label="Storage Nodes" value={num(sto.count)} tint="bg-amber-100 text-amber-600" />
      </div>

      {/* node breakdown */}
      <div className="grid lg:grid-cols-2 gap-5">
        <div data-tour="dc-validator" className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Server size={18} className="text-violet-600" /> Validator Nodes</h3>
          <div className="space-y-3">
            {[["Nodes sold", num(val.count)], ["Revenue", money(val.revenue)],
              ["Blocks validated", num(val.blocks)], ["Rewards earned", num(val.rewards)],
              ["Active now", num(ns.activeValidatorNodes)], ["Blocks today", num(ns.totalBlocksToday)],
              ["Staked nodes", num(nst.staked_nodes)],
              ["Staking required (DGC)", num(nst.requirement)]].map(([l, v]) => (
              <div key={l} className="flex items-center justify-between">
                <span className="text-sm text-ink-500">{l}</span>
                <span className="text-sm font-bold text-ink-900 tabular-nums">{v}</span>
              </div>
            ))}
          </div>
        </div>
        <div data-tour="dc-storage" className="card p-5">
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

      {/* staking management — the on-chain staking contract */}
      <div className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <h3 className="font-bold text-ink-900 flex items-center gap-2"><Lock size={18} className="text-violet-600" /> Staking</h3>
          {st.contract_address && (
            <a href={st.explorer_url ? `${st.explorer_url}/address/${st.contract_address}` : undefined}
              target="_blank" rel="noreferrer"
              className="text-xs text-brand-600 inline-flex items-center gap-1 hover:underline font-mono">
              {shortAddr(st.contract_address)} <ExternalLink size={11} />
            </a>
          )}
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div><p className="text-2xl font-extrabold text-ink-900 tabular-nums">{num(st.total_staked)}</p><p className="text-xs text-ink-400">DGCC staked</p></div>
          <div><p className="text-2xl font-extrabold text-ink-900 tabular-nums">{num(st.reward_pool)}</p><p className="text-xs text-ink-400">Reward pool (DGCC)</p></div>
          <div><p className="text-2xl font-extrabold text-ink-900 tabular-nums">{num(st.registrations)}</p><p className="text-xs text-ink-400">Active registrations</p></div>
          <div><p className="text-2xl font-extrabold text-ink-900 tabular-nums">{num(st.stakers)}</p><p className="text-xs text-ink-400">Stakers</p></div>
        </div>
        {st.owner && (
          <p className="text-xs text-ink-400 mt-3">Contract owner <span className="font-mono text-ink-600">{shortAddr(st.owner)}</span></p>
        )}
        {tranches.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm min-w-[420px]">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide border-b border-ink-100">
                  <th className="py-2 pr-4 font-semibold">Stage</th>
                  <th className="py-2 px-4 font-semibold text-right">Lock (days)</th>
                  <th className="py-2 px-4 font-semibold text-right">APY</th>
                  <th className="py-2 pl-4 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {tranches.map((t) => (
                  <tr key={t.id} className="border-b border-ink-50">
                    <td className="py-2 pr-4 font-medium text-ink-800">{t.label || `Stage ${t.id + 1}`}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-600">{num(t.days)}</td>
                    <td className="py-2 px-4 text-right tabular-nums font-semibold text-emerald-600">{t.apy}%</td>
                    <td className="py-2 pl-4 text-right">
                      <span className={`badge ${t.active ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{t.active ? "Active" : "Off"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* products & pricing — the node catalogue pulled from DAGChain */}
      {(validators.length > 0 || storage.length > 0 || aprRates.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-5">
          <div className="card p-5">
            <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Package size={18} className="text-brand-600" /> Node Products &amp; Pricing</h3>
            {validators.length > 0 && (
              <>
                <p className="text-[11px] uppercase tracking-wide text-ink-400 font-semibold mb-1">Validator tiers</p>
                <div className="overflow-x-auto mb-4">
                  <table className="w-full text-sm min-w-[380px]">
                    <thead><tr className="text-left text-ink-400 text-[11px] uppercase border-b border-ink-100">
                      <th className="py-1.5 pr-3 font-semibold">Tier</th>
                      <th className="py-1.5 px-3 font-semibold text-right">Price</th>
                      <th className="py-1.5 px-3 font-semibold text-right">Sold / Total</th>
                      <th className="py-1.5 pl-3 font-semibold text-right">Status</th>
                    </tr></thead>
                    <tbody>
                      {validators.map((t) => (
                        <tr key={t.package_id || t.name} className="border-b border-ink-50">
                          <td className="py-1.5 pr-3 font-medium text-ink-800">{t.name}</td>
                          <td className="py-1.5 px-3 text-right tabular-nums text-ink-700">{money(t.price)}</td>
                          <td className="py-1.5 px-3 text-right tabular-nums text-ink-500">{num(t.sold)} / {num(t.total)}</td>
                          <td className="py-1.5 pl-3 text-right"><span className={`badge ${t.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{(t.status || "").replace("_", " ") || "—"}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {storage.length > 0 && (
              <>
                <p className="text-[11px] uppercase tracking-wide text-ink-400 font-semibold mb-1">Storage packages</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[380px]">
                    <thead><tr className="text-left text-ink-400 text-[11px] uppercase border-b border-ink-100">
                      <th className="py-1.5 pr-3 font-semibold">Package</th>
                      <th className="py-1.5 px-3 font-semibold text-right">Price / GB</th>
                      <th className="py-1.5 pl-3 font-semibold text-right">Capacity (GB)</th>
                    </tr></thead>
                    <tbody>
                      {storage.map((p) => (
                        <tr key={p.name} className="border-b border-ink-50">
                          <td className="py-1.5 pr-3 font-medium text-ink-800">{p.name}</td>
                          <td className="py-1.5 px-3 text-right tabular-nums text-ink-700">{money(p.price_per_gb)}</td>
                          <td className="py-1.5 pl-3 text-right tabular-nums text-ink-500">{num(p.min_gb)} – {num(p.max_gb)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>

          {aprRates.length > 0 && (
            <div className="card p-5">
              <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Percent size={18} className="text-emerald-600" /> Reward Rates (APR)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[360px]">
                  <thead><tr className="text-left text-ink-400 text-[11px] uppercase border-b border-ink-100">
                    <th className="py-1.5 pr-3 font-semibold">Node</th>
                    <th className="py-1.5 px-3 font-semibold">Tier</th>
                    <th className="py-1.5 px-3 font-semibold text-right">APR</th>
                    <th className="py-1.5 pl-3 font-semibold text-right">Min lock</th>
                  </tr></thead>
                  <tbody>
                    {aprRates.map((r, i) => (
                      <tr key={i} className="border-b border-ink-50">
                        <td className="py-1.5 pr-3 text-ink-600">{r.kind}</td>
                        <td className="py-1.5 px-3 font-medium text-ink-800">{r.tier}</td>
                        <td className="py-1.5 px-3 text-right tabular-nums font-semibold text-emerald-600">{r.apr}%</td>
                        <td className="py-1.5 pl-3 text-right tabular-nums text-ink-500">{num(r.min_lock_days)}d</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* platform + community */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-5">
        <Tile icon={Activity} label="Transactions" value={num(dash.totalTransactions)} tint="bg-sky-100 text-sky-600" />
        <Tile icon={Layers} label="Total Volume" value={num(dash.totalVolume)} tint="bg-ink-100 text-ink-500" />
        <Tile icon={Coins} label="DGC held (users)" value={num(p.dgc)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Lock} label="Staked (DGCC)" value={num(st.total_staked)} tint="bg-violet-100 text-violet-600" />
        <Tile icon={Users} label="Referrals" value={num(p.refs)} tint="bg-rose-100 text-rose-500" />
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <Link to="/dagchain-users" data-tour="dc-users" className="card p-5 flex items-center justify-between hover:shadow-soft transition">
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
