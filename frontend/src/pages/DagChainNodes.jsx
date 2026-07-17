import { useState } from "react";
import { Link } from "react-router-dom";
import { Server, HardDrive, Search, Download, Coins, Activity } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 4 });
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const STATUS_TINT = { active: "bg-emerald-50 text-emerald-700", failed: "bg-rose-50 text-rose-600", pending: "bg-amber-50 text-amber-700" };

function Stat({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-4">
      <div className={`grid place-items-center w-9 h-9 rounded-xl ${tint}`}><Icon size={16} /></div>
      <p className="text-xl font-extrabold text-ink-900 mt-2 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400">{label}</p>
    </div>
  );
}

export default function DagChainNodes() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");

  usePolling(() => {
    const params = { page_size: 500 };
    if (q) params.search = q;
    if (kind) params.kind = kind;
    api.get("/dagchain-nodes/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load DAGChain nodes."));
  }, 8000, [q, kind]);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading nodes…" />;

  const rows = d.results || d || [];
  const totals = rows.reduce((a, r) => ({
    rev: a.rev + Number(r.purchase_price || 0),
    rewards: a.rewards + Number(r.rewards_earned || 0),
    blocks: a.blocks + Number(r.blocks_validated || 0),
  }), { rev: 0, rewards: 0, blocks: 0 });

  const exportCsv = () => {
    const head = ["Kind", "Node Key", "Package", "Owner", "RM", "Price", "Currency", "Status", "Payment", "Uptime %", "Blocks", "Rewards", "Pending", "Claimed", "APY", "Capacity", "Staked", "Opened"];
    const body = rows.map((r) => [r.kind, r.node_key, r.package, r.customer_name, r.rm, r.purchase_price, r.currency, r.status, r.payment_status, r.uptime, r.blocks_validated, r.rewards_earned, r.pending_rewards, r.claimed_rewards, r.effective_apy, r.capacity, r.is_staked, r.opened_at]);
    const csv = [head, ...body].map((l) => l.map((x) => `"${String(x ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "dagchain-nodes.csv"; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Server className="text-brand-600" /> DAGChain Nodes</h1>
          <p className="text-sm text-ink-400">Validator &amp; storage nodes — price, uptime, blocks, rewards, APY</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 chip !py-2"><Search size={14} className="text-ink-400" />
            <input className="bg-transparent outline-none text-sm w-36" placeholder="Node / owner…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <select className="input !w-auto !py-1.5 text-sm" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="">All nodes</option>
            <option value="validator">Validator</option>
            <option value="storage">Storage</option>
          </select>
          <button className="btn-ghost border border-ink-200 text-sm" onClick={exportCsv}><Download size={14} /> CSV</button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat icon={Server} label="Nodes" value={rows.length} tint="bg-brand-100 text-brand-600" />
        <Stat icon={Coins} label="Revenue" value={money(totals.rev)} tint="bg-emerald-100 text-emerald-600" />
        <Stat icon={Activity} label="Blocks validated" value={num(totals.blocks)} tint="bg-violet-100 text-violet-600" />
        <Stat icon={Coins} label="Rewards earned" value={num(totals.rewards)} tint="bg-amber-100 text-amber-600" />
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[1000px]">
            <thead>
              <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">Package / Node</th>
                <th className="py-3 px-4 font-semibold">Owner</th>
                <th className="py-3 px-4 font-semibold text-right">Price</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Uptime</th>
                <th className="py-3 px-4 font-semibold text-right">Blocks</th>
                <th className="py-3 px-4 font-semibold text-right">Rewards</th>
                <th className="py-3 px-4 font-semibold text-right">APY</th>
                <th className="py-3 px-4 font-semibold">Opened</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-ink-100 hover:bg-ink-50/60">
                  <td className="py-2.5 px-4">
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold">
                      {r.kind === "validator" ? <Server size={13} className="text-violet-500" /> : <HardDrive size={13} className="text-amber-500" />}
                      {r.kind}
                    </span>
                  </td>
                  <td className="py-2.5 px-4">
                    <p className="font-medium text-ink-800">{r.package || "—"}</p>
                    <p className="text-[11px] text-ink-400 font-mono">{r.node_key}{r.capacity ? ` · ${r.capacity}` : ""}</p>
                  </td>
                  <td className="py-2.5 px-4">
                    {r.customer ? <Link to={`/customers/${r.customer}`} className="text-brand-700 hover:underline">{r.customer_name}</Link> : <span className="text-ink-400">—</span>}
                    <p className="text-[11px] text-ink-400">{r.rm || "Unassigned"}</p>
                  </td>
                  <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-emerald-600">{money(r.purchase_price)}</td>
                  <td className="py-2.5 px-4"><span className={`badge ${STATUS_TINT[r.status] || "bg-ink-100 text-ink-500"}`}>{r.status || "—"}</span></td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-600">{num(r.uptime)}%</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-violet-600">{num(r.blocks_validated)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-amber-600">{num(r.rewards_earned)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{num(r.effective_apy)}%</td>
                  <td className="py-2.5 px-4 text-ink-500 whitespace-nowrap">{date(r.opened_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState title="Koi node nahi mila" hint="Filter badlo ya DAGChain sync karo." />}
      </div>
    </div>
  );
}
