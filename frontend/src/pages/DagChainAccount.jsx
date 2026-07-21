import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Coins, Wallet, Users, Server, HardDrive, ArrowLeft, RefreshCcw,
  ShieldCheck, Boxes, Gauge,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 4 });
const int = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
const dt = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const short = (w) => (w ? `${w.slice(0, 8)}…${w.slice(-6)}` : "—");

function Tile({ icon: Icon, label, value, tint, sub }) {
  return (
    <div className="card p-4">
      <div className={`grid place-items-center w-9 h-9 rounded-xl ${tint}`}><Icon size={16} /></div>
      <p className="text-lg font-extrabold text-ink-900 mt-2 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400">{label}</p>
      {sub != null && <p className="text-[11px] text-ink-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function Section({ icon: Icon, title, count, actions, children, tour }) {
  return (
    <div data-tour={tour} className="card p-0 overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-ink-100">
        <Icon size={16} className="text-brand-600" />
        <h3 className="font-bold text-ink-900">{title}</h3>
        {count != null && <span className="badge bg-ink-100 text-ink-500">{count}</span>}
        {actions && <div className="ml-auto flex flex-wrap items-center gap-2">{actions}</div>}
      </div>
      {children}
    </div>
  );
}

export default function DagChainAccount() {
  const { id } = useParams();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [kind, setKind] = useState("");    // ""=all | validator | storage
  const [status, setStatus] = useState(""); // node status filter

  usePolling(() => {
    api.get(`/reports/dagchain-account/`, { params: { customer: id } })
      .then((r) => { setD(r.data); setErr(r.data?.error || ""); })
      .catch((e) => setErr(e.response?.data?.error || "Failed to load DAGChain account."));
  }, 12000, [id]);

  if (err) return <EmptyState title="Not available" hint={err} />;
  if (!d) return <Spinner label="Loading DAGChain account…" />;

  const p = d.profile || {};
  const t = d.totals || {};
  const nodes = d.nodes || [];
  const statuses = [...new Set(nodes.map((n) => n.status).filter(Boolean))].sort();
  const nodesShown = nodes.filter((n) =>
    (!kind || n.kind === kind) && (!status || n.status === status));

  return (
    <div className="space-y-5">
      {/* header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/dagchain-users" className="text-xs text-brand-600 inline-flex items-center gap-1 hover:underline"><ArrowLeft size={12} /> All Users</Link>
          <h1 className="text-2xl font-extrabold text-ink-900 mt-1">{d.name || "DAGChain User"}</h1>
          <p className="text-sm text-ink-400 flex flex-wrap items-center gap-x-2">
            <span className="font-mono" title={p.wallet_address}>{short(p.wallet_address)}</span>
            {d.email ? <span>· {d.email}</span> : null}
            <span>· <ShieldCheck size={12} className="inline -mt-0.5" /> KYC {p.kyc_status || "—"}</span>
            {d.rm ? <span>· RM: <b className="text-ink-600">{d.rm}</b></span> : null}
            <span>· <Link to={`/customers/${d.customer_id}`} className="text-brand-600 hover:underline">Customer 360</Link></span>
          </p>
        </div>
        <span className="text-xs text-ink-400 inline-flex items-center gap-1"><RefreshCcw size={12} /> live · every 12s</span>
      </div>

      {/* metric tiles */}
      <div data-tour="dca-metrics" className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <Tile icon={Coins} label="DGC Balance" value={num(p.dgc_balance)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Wallet} label="Fuel Wallet" value={money(p.fuel_wallet_usd)} tint="bg-sky-100 text-sky-600" />
        <Tile icon={Users} label="Referrals" value={int(p.referral_count)} tint="bg-brand-100 text-brand-600" />
        <Tile icon={Coins} label="Ref. Earnings" value={num(p.total_referral_earnings)} tint="bg-amber-100 text-amber-600" />
        <Tile icon={Server} label="Validator Nodes" value={int(t.validator_nodes)} tint="bg-violet-100 text-violet-600" />
        <Tile icon={HardDrive} label="Storage Nodes" value={int(t.storage_nodes)} tint="bg-indigo-100 text-indigo-600" />
        <Tile icon={Coins} label="Node Spend" value={money(t.node_spend)} tint="bg-rose-100 text-rose-500" />
        <Tile icon={Gauge} label="Logins" value={int(p.login_count)} tint="bg-ink-100 text-ink-600" />
      </div>

      {/* identity / wallet */}
      <Section icon={Boxes} title="Profile & Wallet" tour="dca-profile">
        <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-y-3 gap-x-4 text-sm">
          {[
            ["User Type", p.user_type || "—"],
            ["Account Status", p.status || "—"],
            ["KYC Status", p.kyc_status || "—"],
            ["Email Verified", p.email_verified ? "Yes" : "No"],
            ["Social Login", p.social_provider || "—"],
            ["Referral Code", p.referral_code || "—"],
            ["Rewards Earned", num(t.rewards_earned)],
            ["Pending Rewards", num(t.pending_rewards)],
            ["Claimed Rewards", num(t.claimed_rewards)],
            ["Total Staked (DGC)", num(t.staked)],
            ["Staked Nodes", `${t.staked_nodes || 0} of ${t.nodes || 0}`],
            ["Joined", dt(p.joined_at)],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[11px] text-ink-400 uppercase tracking-wide">{k}</p>
              <p className="font-semibold text-ink-800 break-words">{v}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* nodes */}
      <Section icon={Server} title="Nodes" count={nodesShown.length} tour="dca-nodes"
        actions={nodes.length > 0 && (
          <>
            <div className="flex items-center rounded-lg bg-ink-100 p-0.5 text-xs">
              {[["", "All"], ["validator", "Validator"], ["storage", "Storage"]].map(([v, label]) => (
                <button key={v} onClick={() => setKind(v)}
                  className={`px-2.5 py-1 rounded-md font-semibold ${kind === v ? "bg-white text-ink-900 shadow-sm" : "text-ink-500"}`}>
                  {label}
                </button>
              ))}
            </div>
            {statuses.length > 0 && (
              <select className="input !py-1.5 !text-xs w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="">All statuses</option>
                {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            )}
          </>
        )}>
        {nodesShown.length === 0 ? (
          <EmptyState title={nodes.length ? "No match" : "No nodes"} hint={nodes.length ? "Try adjusting the filters." : "This user hasn't purchased any nodes."} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[960px]">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">Type</th>
                  <th className="py-2.5 px-4">Package</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Price</th>
                  <th className="py-2.5 px-4 text-right">APY</th>
                  <th className="py-2.5 px-4 text-right">Uptime</th>
                  <th className="py-2.5 px-4 text-right">Blocks</th>
                  <th className="py-2.5 px-4 text-right">Earned</th>
                  <th className="py-2.5 px-4 text-right">Pending</th>
                  <th className="py-2.5 px-4 text-right">Staked</th>
                  <th className="py-2.5 px-4">Capacity</th>
                  <th className="py-2.5 px-4">Opened</th>
                </tr>
              </thead>
              <tbody>
                {nodesShown.map((n) => (
                  <tr key={n.id} className="border-t border-ink-100 hover:bg-ink-50/60">
                    <td className="py-2 px-4">
                      <span className={`badge inline-flex items-center gap-1 ${n.kind === "validator" ? "bg-violet-50 text-violet-700" : "bg-indigo-50 text-indigo-700"}`}>
                        {n.kind === "validator" ? <Server size={11} /> : <HardDrive size={11} />}{n.kind}
                      </span>
                    </td>
                    <td className="py-2 px-4 font-medium text-ink-800">{n.package || "—"}{n.is_staked && <span className="ml-1 badge bg-emerald-50 text-emerald-700">staked</span>}</td>
                    <td className="py-2 px-4"><span className={`badge ${(n.status || "").toLowerCase() === "active" ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{n.status || "—"}</span></td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-700">{money(n.purchase_price)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-emerald-600">{n.effective_apy ? `${num(n.effective_apy)}%` : "—"}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-500">{n.uptime ? `${num(n.uptime)}%` : "—"}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-500">{n.kind === "validator" ? int(n.blocks_validated) : "—"}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-amber-600">{num(n.rewards_earned)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-500">{num(n.pending_rewards)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-violet-600">{n.staked_amount ? num(n.staked_amount) : (n.staking_requirement ? `0 / ${num(n.staking_requirement)}` : "—")}</td>
                    <td className="py-2 px-4 text-ink-500">{n.kind === "storage" ? (n.capacity || "—") : "—"}</td>
                    <td className="py-2 px-4 text-ink-500 whitespace-nowrap">{dt(n.opened_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}
