import { useState } from "react";
import { Link } from "react-router-dom";
import { Users, Search, Download, Coins, Server, ShieldCheck } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 4 });
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const short = (w) => (w ? `${w.slice(0, 6)}…${w.slice(-4)}` : "—");
const PAGE = 25;

export default function DagChainUsers() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [kyc, setKyc] = useState("");
  const [page, setPage] = useState(1);

  usePolling(() => {
    const params = { page, page_size: PAGE };
    if (q) params.search = q;
    if (kyc) params.kyc_status = kyc;
    api.get("/dagchain-profiles/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load DAGChain users."));
  }, 8000, [q, kyc, page]);

  const exportCsv = async () => {
    const { data } = await api.get("/dagchain-profiles/", { params: { page_size: 5000 } });
    const rows = data?.results || data || [];
    const head = ["Name", "Email", "Wallet", "Status", "KYC", "DGC Balance", "Fuel USD", "Referral Code", "Referrals", "Referral Earnings", "Validator Nodes", "Storage Nodes", "Logins", "Joined", "RM"];
    const body = rows.map((r) => [r.display_name || r.customer_name, r.email, r.wallet_address, r.status, r.kyc_status, r.dgc_balance, r.fuel_wallet_usd, r.referral_code, r.referral_count, r.total_referral_earnings, r.validator_nodes_count, r.storage_nodes_count, r.login_count, r.joined_at, r.rm]);
    const csv = [head, ...body].map((l) => l.map((x) => `"${String(x ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "dagchain-users.csv"; a.click(); URL.revokeObjectURL(url);
  };

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading DAGChain users…" />;

  const rows = d.results || d || [];
  const total = d.count ?? rows.length;
  const pages = Math.max(1, Math.ceil(total / PAGE));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Users className="text-brand-600" /> DAGChain Users</h1>
          <p className="text-sm text-ink-400">{total} users · wallet, DGC balance, referrals, KYC, nodes</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div data-tour="dcu-search" className="flex items-center gap-1.5 chip !py-2"><Search size={14} className="text-ink-400" />
            <input className="bg-transparent outline-none text-sm w-40" placeholder="Name / email / wallet…" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
          </div>
          <select data-tour="dcu-kyc" className="input !w-auto !py-1.5 text-sm" value={kyc} onChange={(e) => { setPage(1); setKyc(e.target.value); }}>
            <option value="">All KYC</option>
            <option value="not_started">Not started</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button data-tour="dcu-export" className="btn-ghost border border-ink-200 text-sm" onClick={exportCsv}><Download size={14} /> CSV</button>
        </div>
      </div>

      <div data-tour="dcu-table" className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[980px]">
            <thead>
              <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                <th className="py-3 px-4 font-semibold">User</th>
                <th className="py-3 px-4 font-semibold">Wallet</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">KYC</th>
                <th className="py-3 px-4 font-semibold text-right">DGC</th>
                <th className="py-3 px-4 font-semibold text-right">Referrals</th>
                <th className="py-3 px-4 font-semibold text-right">Ref. Earnings</th>
                <th className="py-3 px-4 font-semibold text-center">Nodes (V/S)</th>
                <th className="py-3 px-4 font-semibold text-right">Logins</th>
                <th className="py-3 px-4 font-semibold">Joined</th>
                <th className="py-3 px-4 font-semibold">RM</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-ink-100 hover:bg-ink-50/60">
                  <td className="py-2.5 px-4">
                    <Link to={`/dagchain-account/${r.customer}`} className="font-medium text-brand-700 hover:underline">{r.display_name || r.email || r.customer_name || short(r.wallet_address) || "—"}</Link>
                    <div className="text-[11px] text-ink-400">{r.email || short(r.wallet_address)}</div>
                  </td>
                  <td className="py-2.5 px-4 font-mono text-xs text-ink-500" title={r.wallet_address}>{short(r.wallet_address)}</td>
                  <td className="py-2.5 px-4"><span className={`badge ${r.status === "ACTIVE" ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{r.status}</span></td>
                  <td className="py-2.5 px-4"><span className="text-xs text-ink-500 inline-flex items-center gap-1"><ShieldCheck size={12} /> {r.kyc_status || "—"}</span></td>
                  <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-emerald-600">{num(r.dgc_balance)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums">{r.referral_count}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-amber-600">{num(r.total_referral_earnings)}</td>
                  <td className="py-2.5 px-4 text-center">
                    <span className="inline-flex items-center gap-1 text-xs">
                      <Server size={11} className="text-violet-500" />{r.validator_nodes_count}
                      <span className="text-ink-300">/</span>{r.storage_nodes_count}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{r.login_count}</td>
                  <td className="py-2.5 px-4 text-ink-500 whitespace-nowrap">{date(r.joined_at)}</td>
                  <td className="py-2.5 px-4 text-xs">{r.rm || <span className="text-rose-500">Unassigned</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState title="No users found" hint="Try adjusting your filters, or sync DAGChain." />}
        {rows.length > 0 && (
          <div className="flex items-center justify-between p-4 border-t border-ink-100">
            <span className="text-xs text-ink-400 font-mono">Page {page} of {pages} · {total} users</span>
            <div className="flex gap-2">
              <button className="btn-ghost border border-ink-200 text-sm disabled:opacity-40" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>‹ Prev</button>
              <button className="btn-ghost border border-ink-200 text-sm disabled:opacity-40" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next ›</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
