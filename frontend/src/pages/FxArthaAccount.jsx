import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Wallet, TrendingUp, Layers, Gauge, ArrowLeft, Activity, ClipboardList,
  BookOpen, Users, RefreshCcw, Search, CandlestickChart,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState } from "../components/ui";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
const dt = (v) => (v ? new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—");
const pnlColor = (v) => (Number(v) > 0 ? "text-emerald-600" : Number(v) < 0 ? "text-rose-500" : "text-ink-600");

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

function Section({ icon: Icon, title, count, actions, children }) {
  return (
    <div className="card p-0 overflow-hidden">
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

export default function FxArthaAccount() {
  const { id } = useParams();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [psym, setPsym] = useState("");   // position symbol filter
  const [lq, setLq] = useState("");       // ledger search
  const [ltype, setLtype] = useState(""); // ledger type filter
  const [lfrom, setLfrom] = useState(""); // ledger date from
  const [lto, setLto] = useState("");     // ledger date to
  const [tst, setTst] = useState("");     // trades status filter: ""=all|open|closed

  usePolling(() => {
    api.get(`/reports/fxartha-account/`, { params: { customer: id } })
      .then((r) => { setD(r.data); setErr(r.data?.error || ""); })
      .catch((e) => setErr(e.response?.data?.error || "Failed to load FX Artha account."));
  }, 12000, [id]);

  if (err) return <EmptyState title="Not available" hint={err} />;
  if (!d) return <Spinner label="Loading FX Artha account…" />;

  const a = d.account || {};
  const pos = d.positions || [];
  const orders = d.orders || [];
  const ledger = d.ledger || [];
  const trades = d.trades || [];
  const ib = d.ib || {};

  const tradesShown = tst ? trades.filter((t) => (t.status || "").toLowerCase() === tst) : trades;
  const symbols = [...new Set(pos.map((p) => p.symbol))].sort();
  const posShown = psym ? pos.filter((p) => p.symbol === psym) : pos;
  const ledTypes = [...new Set(ledger.map((l) => l.type))].sort();
  const ledShown = ledger.filter((l) => {
    if (ltype && l.type !== ltype) return false;
    if (lq && !`${l.description || ""} ${l.type || ""}`.toLowerCase().includes(lq.toLowerCase())) return false;
    const day = (l.created_at || "").slice(0, 10);
    if (lfrom && day < lfrom) return false;
    if (lto && day > lto) return false;
    return true;
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/fxartha-traders" className="text-xs text-brand-600 inline-flex items-center gap-1 hover:underline"><ArrowLeft size={12} /> All Traders</Link>
          <h1 className="text-2xl font-extrabold text-ink-900 mt-1">{a.name || "Trader"}</h1>
          <p className="text-sm text-ink-400">
            {a.account_type || "—"} · {a.broker || "FXArtha"} · {a.currency || "USD"}
            {a.accounts?.length ? ` · ${a.accounts.join(", ")}` : ""}
            {" · "}<Link to={`/customers/${d.customer_id}`} className="text-brand-600 hover:underline">Customer 360</Link>
          </p>
        </div>
        <span className="text-xs text-ink-400 inline-flex items-center gap-1"><RefreshCcw size={12} /> live · every 12s</span>
      </div>

      {/* account metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <Tile icon={Wallet} label="Balance" value={money(a.balance)} tint="bg-brand-100 text-brand-600" />
        <Tile icon={TrendingUp} label="Equity" value={money(a.equity)} tint="bg-emerald-100 text-emerald-600" />
        <Tile icon={Wallet} label="Credit" value={money(a.credit)} tint="bg-amber-100 text-amber-600" />
        <Tile icon={Layers} label="Free Margin" value={money(a.free_margin)} tint="bg-sky-100 text-sky-600" />
        <Tile icon={Layers} label="Margin Used" value={money(a.margin_used)} tint="bg-rose-100 text-rose-500" />
        <Tile icon={Gauge} label="Margin Level" value={`${num(a.margin_level)}%`} tint="bg-indigo-100 text-indigo-600" />
        <Tile icon={Gauge} label="Leverage" value={a.leverage ? `1:${a.leverage}` : "—"} tint="bg-ink-100 text-ink-600" sub={a.swap_free ? "swap-free" : null} />
      </div>

      {/* live positions */}
      <Section icon={Activity} title="Live Positions" count={posShown.length}
        actions={pos.length > 0 && (
          <select className="input !py-1.5 !text-xs w-auto" value={psym} onChange={(e) => setPsym(e.target.value)}>
            <option value="">All symbols</option>
            {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        )}>
        {pos.length === 0 ? (
          <EmptyState title="No open positions" hint="Trader ke koi live trade nahi." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[760px]">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">Symbol</th><th className="py-2.5 px-4">Side</th>
                  <th className="py-2.5 px-4 text-right">Lots</th><th className="py-2.5 px-4 text-right">Open</th>
                  <th className="py-2.5 px-4 text-right">SL</th><th className="py-2.5 px-4 text-right">TP</th>
                  <th className="py-2.5 px-4 text-right">Swap</th><th className="py-2.5 px-4 text-right">Comm.</th>
                </tr>
              </thead>
              <tbody>
                {posShown.map((p) => (
                  <tr key={p.position_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                    <td className="py-2 px-4 font-medium">{p.symbol}</td>
                    <td className="py-2 px-4"><span className={`badge ${p.side === "buy" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>{p.side}</span></td>
                    <td className="py-2 px-4 text-right tabular-nums">{num(p.lots)}</td>
                    <td className="py-2 px-4 text-right tabular-nums">{num(p.open_price)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-400">{p.stop_loss ? num(p.stop_loss) : "—"}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-400">{p.take_profit ? num(p.take_profit) : "—"}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-500">{num(p.swap)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-500">{money(p.commission)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* trades — open + closed, with a status filter */}
      <Section icon={CandlestickChart} title="Trades" count={tradesShown.length}
        actions={trades.length > 0 && (
          <div className="flex items-center rounded-lg bg-ink-100 p-0.5 text-xs">
            {[["", "All"], ["open", "Open"], ["closed", "Closed"]].map(([v, label]) => (
              <button key={v} onClick={() => setTst(v)}
                className={`px-2.5 py-1 rounded-md font-semibold ${tst === v ? "bg-white text-ink-900 shadow-sm" : "text-ink-500"}`}>
                {label}
              </button>
            ))}
          </div>
        )}>
        {tradesShown.length === 0 ? (
          <EmptyState title={trades.length ? "No match" : "No trades"} hint={trades.length ? "Filter badlo." : "Koi trade nahi."} />
        ) : (
          <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
            <table className="w-full text-sm min-w-[860px]">
              <thead className="sticky top-0">
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">Status</th><th className="py-2.5 px-4">Symbol</th>
                  <th className="py-2.5 px-4">Side</th><th className="py-2.5 px-4 text-right">Lots</th>
                  <th className="py-2.5 px-4 text-right">Open</th><th className="py-2.5 px-4 text-right">Close</th>
                  <th className="py-2.5 px-4 text-right">Net P&L</th><th className="py-2.5 px-4 text-right">Brokerage</th>
                  <th className="py-2.5 px-4">Opened</th>
                </tr>
              </thead>
              <tbody>
                {tradesShown.map((tr) => {
                  const open = (tr.status || "").toLowerCase() === "open";
                  return (
                    <tr key={tr.trade_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                      <td className="py-2 px-4"><span className={`badge ${open ? "bg-sky-50 text-sky-700" : "bg-ink-100 text-ink-500"}`}>{tr.status || "—"}</span></td>
                      <td className="py-2 px-4 font-medium">{tr.symbol}</td>
                      <td className="py-2 px-4"><span className={`badge ${tr.side === "buy" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>{tr.side}</span></td>
                      <td className="py-2 px-4 text-right tabular-nums">{num(tr.lots)}</td>
                      <td className="py-2 px-4 text-right tabular-nums">{num(tr.open_price)}</td>
                      <td className="py-2 px-4 text-right tabular-nums text-ink-500">{open ? "—" : num(tr.close_price)}</td>
                      <td className={`py-2 px-4 text-right tabular-nums font-semibold ${open ? "text-ink-400" : pnlColor(tr.net_pnl)}`}>{open ? "—" : money(tr.net_pnl)}</td>
                      <td className="py-2 px-4 text-right tabular-nums text-ink-500">{money(tr.brokerage)}</td>
                      <td className="py-2 px-4 text-ink-500 whitespace-nowrap">{dt(tr.opened_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* orders */}
        <Section icon={ClipboardList} title="Working Orders" count={orders.length}>
          {orders.length === 0 ? (
            <EmptyState title="No pending orders" hint="Koi working/pending order nahi." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                    <th className="py-2.5 px-4">Symbol</th><th className="py-2.5 px-4">Side</th>
                    <th className="py-2.5 px-4 text-right">Lots</th><th className="py-2.5 px-4 text-right">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o, i) => (
                    <tr key={o.order_id || i} className="border-t border-ink-100">
                      <td className="py-2 px-4 font-medium">{o.symbol}</td>
                      <td className="py-2 px-4">{o.side}</td>
                      <td className="py-2 px-4 text-right tabular-nums">{num(o.lots)}</td>
                      <td className="py-2 px-4 text-right tabular-nums">{num(o.price || o.open_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* IB info */}
        <Section icon={Users} title="IB / Referral">
          <div className="p-4 grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
            {[
              ["Is IB", ib.is_ib ? "Yes" : "No"],
              ["IB Level", ib.ib_level ?? "—"],
              ["Upline", ib.ib_upline_email || "—"],
              ["Pending Payout", money(ib.ib_pending_payout)],
              ["Comm./Lot", ib.ib_custom_commission_per_lot != null ? money(ib.ib_custom_commission_per_lot) : "—"],
              ["Comm./Trade", ib.ib_custom_commission_per_trade != null ? money(ib.ib_custom_commission_per_trade) : "—"],
              ["IB Commission", money(ib.ib_commission_total)],
              ["Referral Code", ib.referral_code || "—"],
              ["Referred By", ib.referred_by || "—"],
              ["Referrals", ib.referrals_count ?? 0],
              ["Followers", ib.followers_count ?? 0],
            ].map(([k, v]) => (
              <div key={k}>
                <p className="text-[11px] text-ink-400 uppercase tracking-wide">{k}</p>
                <p className="font-semibold text-ink-800 break-words">{v}</p>
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* ledger */}
      <Section icon={BookOpen} title="Ledger — balance movements" count={ledShown.length}
        actions={ledger.length > 0 && (
          <>
            <div className="chip !py-1.5"><Search size={13} className="text-ink-400" /><input className="bg-transparent outline-none text-xs w-28" placeholder="Search…" value={lq} onChange={(e) => setLq(e.target.value)} /></div>
            <select className="input !py-1.5 !text-xs w-auto" value={ltype} onChange={(e) => setLtype(e.target.value)}>
              <option value="">All types</option>
              {ledTypes.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <label className="chip !py-1.5 text-xs flex items-center gap-1">From <input type="date" className="bg-transparent outline-none text-xs" value={lfrom} onChange={(e) => setLfrom(e.target.value)} /></label>
            <label className="chip !py-1.5 text-xs flex items-center gap-1">To <input type="date" className="bg-transparent outline-none text-xs" value={lto} onChange={(e) => setLto(e.target.value)} /></label>
          </>
        )}>
        {ledShown.length === 0 ? (
          <EmptyState title={ledger.length ? "No match" : "No ledger entries"} hint={ledger.length ? "Filter/search badlo." : "Koi balance movement nahi."} />
        ) : (
          <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead className="sticky top-0">
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">When</th><th className="py-2.5 px-4">Type</th>
                  <th className="py-2.5 px-4">Description</th>
                  <th className="py-2.5 px-4 text-right">Amount</th><th className="py-2.5 px-4 text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                {ledShown.map((l) => (
                  <tr key={l.ledger_id} className="border-t border-ink-100 hover:bg-ink-50/60">
                    <td className="py-2 px-4 text-ink-500 whitespace-nowrap">{dt(l.created_at)}</td>
                    <td className="py-2 px-4"><span className="badge bg-ink-100 text-ink-600">{l.type}</span></td>
                    <td className="py-2 px-4 text-ink-500">{l.description || "—"}</td>
                    <td className={`py-2 px-4 text-right tabular-nums font-medium ${pnlColor(l.amount)}`}>{money(l.amount)}</td>
                    <td className="py-2 px-4 text-right tabular-nums text-ink-600">{money(l.balance_after)}</td>
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
