import { useEffect, useState } from "react";
import {
  TrendingUp, Users, ArrowDownToLine, ArrowUpFromLine, BarChart3,
  Download, Search, ChevronLeft, ChevronRight, AlertCircle, RefreshCw,
} from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";
import { useToast } from "../context/ToastContext";

const pretty = (k) => String(k).replace(/[_-]/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2")
  .replace(/\b\w/g, (c) => c.toUpperCase());
const MONEY = /revenue|balance|equity|deposit|withdraw|commission|brokerage|pnl|p_l|p\/l|profit|amount|net/i;
const fmt = (k, v) => {
  if (v == null) return "—";
  if (typeof v === "number") return MONEY.test(k) ? `$${v.toLocaleString()}` : v.toLocaleString();
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
};

const TABS = ["Dashboard", "Leads", "Customers"];

function DynTable({ items, money }) {
  if (!items?.length) return <EmptyState title="No records" />;
  const cols = Object.keys(items[0]).filter((k) => typeof items[0][k] !== "object");
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
            {cols.map((c) => <th key={c} className="pb-3 px-3 font-semibold whitespace-nowrap">{pretty(c)}</th>)}
          </tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={i} className="border-t border-ink-100 hover:bg-ink-50/70">
              {cols.map((c) => (
                <td key={c} className="py-3 px-3 text-ink-700 whitespace-nowrap tabular-nums">{fmt(c, row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Paged({ endpoint, withImport }) {
  const toast = useToast();
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);

  const load = () => {
    setLoading(true);
    api.get(`/fxartha/${endpoint}/`, { params: { page, per_page: 25, search: search || undefined } })
      .then((r) => setData(r.data)).catch((e) => setData({ error: e.response?.data?.detail || "Failed" }))
      .finally(() => setLoading(false));
  };
  useEffect(() => { const t = setTimeout(load, search ? 350 : 0); return () => clearTimeout(t); }, [page, search]);

  const doImport = async () => {
    setImporting(true);
    try {
      const { data: r } = await api.post("/fxartha/import-leads/", { page, per_page: 100, search });
      toast.success(`Imported ${r.created} leads (${r.skipped} duplicates skipped)`);
    } catch (e) {
      toast.error("Import failed: " + (e.response?.data?.detail || e.message));
    } finally { setImporting(false); }
  };

  const items = data?.items || (Array.isArray(data) ? data : []);
  const total = data?.total ?? items.length;
  const perPage = data?.per_page ?? 25;
  const pages = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="chip !py-2">
          <Search size={16} className="text-ink-400" />
          <input className="text-sm outline-none bg-transparent w-44 text-ink-700" placeholder="Search…"
            value={search} onChange={(e) => { setPage(1); setSearch(e.target.value); }} />
        </div>
        {withImport && (
          <button className="btn-primary" onClick={doImport} disabled={importing}>
            <Download size={16} /> {importing ? "Importing…" : "Import to CRM"}
          </button>
        )}
      </div>
      <div className="card p-5">
        {loading ? <Spinner /> : data?.error ? (
          <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{data.error}</div>
        ) : <DynTable items={items} />}
        {!loading && total > perPage && (
          <div className="flex items-center justify-between pt-4 mt-2 border-t border-ink-100">
            <p className="text-xs text-ink-400">{total} records</p>
            <div className="flex items-center gap-1">
              <button className="btn-ghost px-2.5 py-1.5 disabled:opacity-40" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></button>
              <span className="text-sm font-semibold text-ink-700 px-2">{page} / {pages}</span>
              <button className="btn-ghost px-2.5 py-1.5 disabled:opacity-40" disabled={page >= pages} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FxDashboard() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/fxartha/dashboard/").then((r) => setD(r.data)).catch((e) => setD({ error: e.response?.data?.detail || "Failed" })); }, []);
  if (!d) return <Spinner />;
  if (d.error) return <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{d.error}</div>;
  const entries = Object.entries(d).filter(([, v]) => typeof v !== "object");
  const ICONS = [Users, BarChart3, ArrowDownToLine, ArrowUpFromLine, TrendingUp];
  const tints = ["bg-brand-100 text-brand-600", "bg-violet-100 text-violet-600", "bg-emerald-100 text-emerald-600", "bg-amber-100 text-amber-600", "bg-blue-100 text-blue-600"];
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
      {entries.map(([k, v], i) => {
        const Icon = ICONS[i % ICONS.length];
        return (
          <div key={k} className="card p-5">
            <div className={`grid place-items-center w-11 h-11 rounded-2xl ${tints[i % tints.length]}`}><Icon size={20} /></div>
            <p className="text-2xl font-extrabold text-ink-900 mt-4 tabular-nums">{fmt(k, v)}</p>
            <p className="text-sm text-ink-400 mt-0.5">{pretty(k)}</p>
          </div>
        );
      })}
    </div>
  );
}

export default function FXArtha() {
  const [tab, setTab] = useState("Dashboard");
  const [status, setStatus] = useState(null);

  useEffect(() => { api.get("/fxartha/status/").then((r) => setStatus(r.data)).catch(() => setStatus({ configured: false })); }, []);
  if (!status) return <Spinner label="Loading FX Artha…" />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <TrendingUp className="text-brand-600" /> FX Artha
        </h1>
        <p className="text-sm text-ink-400">Forex trading dashboard, leads &amp; trading accounts (live from FX Artha API)</p>
      </div>

      {!status.configured ? (
        <div className="card p-8 text-center">
          <div className="grid place-items-center w-14 h-14 rounded-2xl bg-amber-50 text-amber-500 mx-auto"><AlertCircle size={26} /></div>
          <h2 className="text-lg font-extrabold text-ink-900 mt-4">FX Artha API configured nahi</h2>
          <p className="text-sm text-ink-500 mt-1 max-w-md mx-auto">
            Backend ke <code className="bg-ink-100 px-1.5 py-0.5 rounded text-brand-600">.env</code> me ye daalo aur restart karo:
          </p>
          <pre className="text-left text-xs bg-ink-900 text-ink-100 rounded-xl p-4 mt-4 max-w-md mx-auto overflow-x-auto">FXARTHA_API_URL=https://&lt;admin-host&gt;/api/v1/crm
FXARTHA_API_KEY=&lt;your-key&gt;</pre>
          <button className="btn-ghost border border-ink-200 mt-4" onClick={() => window.location.reload()}><RefreshCw size={15} /> Recheck</button>
        </div>
      ) : (
        <>
          <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit">
            {TABS.map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${tab === t ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
                {t}
              </button>
            ))}
          </div>
          {tab === "Dashboard" && <FxDashboard />}
          {tab === "Leads" && <Paged endpoint="leads" withImport />}
          {tab === "Customers" && <Paged endpoint="customers" />}
        </>
      )}
    </div>
  );
}
