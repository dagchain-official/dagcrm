import { useState } from "react";
import { Link } from "react-router-dom";
import { LineChart, Users, CandlestickChart, Coins, Download, Search, Repeat } from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
const int = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

function Stat({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-4">
      <div className={`grid place-items-center w-9 h-9 rounded-xl ${tint}`}><Icon size={16} /></div>
      <p className="text-xl font-extrabold text-ink-900 mt-2 tabular-nums">{value}</p>
      <p className="text-xs text-ink-400">{label}</p>
    </div>
  );
}

export default function FxArthaTraders() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  usePolling(() => {
    const params = {};
    if (q) params.q = q;
    if (from) params.from = from;
    if (to) params.to = to;
    api.get("/reports/fxartha-traders/", { params })
      .then((r) => { setD(r.data); setErr(""); })
      .catch(() => setErr("Failed to load FXArtha traders."));
  }, 6000, [q, from, to]);

  const exportCsv = () => {
    const rows = d?.rows || [];
    const head = ["Trader", "Email", "Phone", "Country", "RM", "Date", "Lots", "Trades", "Brokerage", "Commission", "Net Revenue", "Deposits", "Withdrawals", "Net AUM", "Insurance", "Staking", "Trading Loss"];
    const body = rows.map((r) => [r.name, r.email, r.phone, r.country, r.rm || "", r.date || "", r.lots, r.trades, r.brokerage, r.commission, r.net_revenue, r.deposits, r.withdrawals, r.net_aum, r.insurance, r.staking, r.trading_loss]);
    const csv = [head, ...body].map((line) => line.map((x) => `"${String(x ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "fxartha-traders.csv"; a.click(); URL.revokeObjectURL(url);
  };

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading FXArtha traders…" />;

  const t = d.totals || {};
  const rows = d.rows || [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><LineChart className="text-brand-600" /> FXArtha Traders</h1>
          <p className="text-sm text-ink-400">Full details for every trader — lots, brokerage, deposits/withdrawals, date, RM</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div data-tour="fxt-search" className="flex items-center gap-1.5 chip !py-2"><Search size={14} className="text-ink-400" /><input className="bg-transparent outline-none text-sm w-36" placeholder="Search trader…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <label data-tour="fxt-dates" className="chip !py-2 text-xs flex items-center gap-1">From <input type="date" className="bg-transparent outline-none text-xs" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <label className="chip !py-2 text-xs flex items-center gap-1">To <input type="date" className="bg-transparent outline-none text-xs" value={to} onChange={(e) => setTo(e.target.value)} /></label>
          <button data-tour="fxt-export" className="btn-ghost border border-ink-200 text-sm" onClick={exportCsv}><Download size={14} /> CSV</button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        <Stat icon={Users} label="Traders" value={t.traders || 0} tint="bg-brand-100 text-brand-600" />
        <Stat icon={CandlestickChart} label="Total Lots" value={num(t.lots)} tint="bg-violet-100 text-violet-600" />
        <Stat icon={Repeat} label="Total Trades" value={int(t.trades)} tint="bg-amber-100 text-amber-600" />
        <Stat icon={Coins} label="Brokerage" value={money(t.brokerage)} tint="bg-emerald-100 text-emerald-600" />
        <Stat icon={Coins} label="Deposits" value={money(t.deposits)} tint="bg-sky-100 text-sky-600" />
        <Stat icon={Coins} label="Withdrawals" value={money(t.withdrawals)} tint="bg-rose-100 text-rose-500" />
      </div>

      <div data-tour="fxt-table" className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[1000px]">
            <thead>
              <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                <th className="py-3 px-4 font-semibold">Trader</th>
                <th className="py-3 px-4 font-semibold">Country</th>
                <th className="py-3 px-4 font-semibold">RM</th>
                <th className="py-3 px-4 font-semibold">Date</th>
                <th className="py-3 px-4 font-semibold text-right">Lots</th>
                <th className="py-3 px-4 font-semibold text-right">Trades</th>
                <th className="py-3 px-4 font-semibold text-right">Brokerage</th>
                <th className="py-3 px-4 font-semibold text-right">Deposits</th>
                <th className="py-3 px-4 font-semibold text-right">Withdrawals</th>
                <th className="py-3 px-4 font-semibold text-right">Net AUM</th>
                <th className="py-3 px-4 font-semibold text-right">Trading Loss</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.customer_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                  <td className="py-2.5 px-4">
                    <Link to={`/fxartha-account/${r.customer_id}`} className="font-medium text-brand-700 hover:underline">{r.name}</Link>
                    <div className="text-[11px] text-ink-400">{r.email || "—"}</div>
                  </td>
                  <td className="py-2.5 px-4 text-ink-500">{r.country || "—"}</td>
                  <td className="py-2.5 px-4">{r.rm || <span className="text-rose-500 text-xs">Unassigned</span>}</td>
                  <td className="py-2.5 px-4 text-ink-500 whitespace-nowrap">{date(r.date)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums font-semibold text-violet-600">{num(r.lots)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-amber-600">{int(r.trades)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-emerald-600">{money(r.brokerage)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-600">{money(r.deposits)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-rose-500">{money(r.withdrawals)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-700">{money(r.net_aum)}</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-ink-500">{money(r.trading_loss)}</td>
                </tr>
              ))}
            </tbody>
            {rows.length > 0 && (
              <tfoot>
                <tr className="border-t-2 border-ink-200 font-bold bg-ink-50">
                  <td className="py-3 px-4" colSpan={4}>Total ({t.traders})</td>
                  <td className="py-3 px-4 text-right tabular-nums text-violet-700">{num(t.lots)}</td>
                  <td className="py-3 px-4 text-right tabular-nums text-amber-700">{int(t.trades)}</td>
                  <td className="py-3 px-4 text-right tabular-nums text-emerald-700">{money(t.brokerage)}</td>
                  <td className="py-3 px-4 text-right tabular-nums">{money(t.deposits)}</td>
                  <td className="py-3 px-4 text-right tabular-nums text-rose-600">{money(t.withdrawals)}</td>
                  <td className="py-3 px-4 text-right tabular-nums">{money(t.net_aum)}</td>
                  <td className="py-3 px-4 text-right tabular-nums">{money(t.trading_loss)}</td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
        {rows.length === 0 && <EmptyState title="No traders found" hint="Try adjusting your filters, or sync FXArtha." />}
      </div>
    </div>
  );
}
