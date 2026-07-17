import { useEffect, useState } from "react";
import {
  Facebook, Chrome, MessageCircle, Linkedin, Music2, Globe, Send,
  Plug, Copy, RefreshCw, Zap, CheckCircle2, Circle, X, LineChart, RefreshCcw,
  Plus, Building2, Trash2,
} from "lucide-react";
import api from "../api/client";
import { Spinner, Modal } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

const ICONS = {
  meta: { Icon: Facebook, color: "bg-blue-100 text-blue-600" },
  google: { Icon: Chrome, color: "bg-rose-100 text-rose-500" },
  whatsapp: { Icon: MessageCircle, color: "bg-emerald-100 text-emerald-600" },
  linkedin: { Icon: Linkedin, color: "bg-sky-100 text-sky-700" },
  tiktok: { Icon: Music2, color: "bg-ink-200 text-ink-700" },
  website: { Icon: Globe, color: "bg-violet-100 text-violet-600" },
  telegram: { Icon: Send, color: "bg-cyan-100 text-cyan-600" },
  fxartha: { Icon: LineChart, color: "bg-indigo-100 text-indigo-600" },
};
const ago = (v) => {
  if (!v) return "never";
  const s = Math.floor((Date.now() - new Date(v)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export default function Integrations() {
  const toast = useToast();
  const { user } = useAuth();
  const businesses = user?.businesses || [];
  const [list, setList] = useState(null);
  const [catalogue, setCatalogue] = useState([]);
  const [active, setActive] = useState(null);   // connection being managed
  const [cfg, setCfg] = useState({});
  const [auto, setAuto] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [adding, setAdding] = useState(null);   // {platform, business, name} while creating

  const load = () => api.get("/integrations/connections/").then((r) => setList(r.data)).catch(() => setList([]));
  useEffect(() => {
    load();
    api.get("/integrations/connections/catalogue/").then((r) => setCatalogue(r.data)).catch(() => setCatalogue([]));
  }, []);

  const open = (c) => { setActive(c); setCfg(c.config || {}); setAuto(c.auto_assign); };

  const openAdd = () => setAdding({ platform: "", business: "", name: "" });
  const createConn = async () => {
    if (!adding.platform) return toast.error("Pick a platform");
    try {
      const { data } = await api.post("/integrations/connections/", {
        platform: adding.platform,
        business: adding.business || null,
        name: adding.name || "",
        status: "disconnected",
      });
      setAdding(null);
      await load();
      open(data);   // jump straight into the manage modal
      toast.success(`${data.label} added — now connect it`);
    } catch (e) {
      const d = e.response?.data;
      toast.error(d?.non_field_errors?.[0] || d?.detail || "This platform already exists for this business");
    }
  };
  const removeConn = async () => {
    if (!window.confirm(`Delete "${active.label}"? Its leads are kept; only the connection is removed.`)) return;
    await api.delete(`/integrations/connections/${active.id}/`);
    setActive(null); load(); toast.info("Integration removed");
  };

  const connect = async () => {
    const { data } = await api.post(`/integrations/connections/${active.id}/connect/`, { config: cfg, auto_assign: auto });
    setActive(data); load(); toast.success(`${data.label} connected`);
  };
  const disconnect = async () => {
    const { data } = await api.post(`/integrations/connections/${active.id}/disconnect/`);
    setActive(data); load(); toast.info(`${data.label} disconnected`);
  };
  const regen = async () => {
    const { data } = await api.post(`/integrations/connections/${active.id}/regenerate_secret/`);
    setActive(data); load(); toast.success("New secret generated");
  };
  const sendTest = async () => {
    const { data } = await api.post(`/integrations/connections/${active.id}/send_test/`);
    setActive(data); load();
    toast.success(data.created ? "Test lead ingested! Check Leads page" : "Test ran (duplicate skipped)");
  };
  const copy = (t) => { navigator.clipboard?.writeText(t); toast.info("Copied"); };
  const sync = async () => {
    setSyncing(true);
    try {
      const { data } = await api.post(`/integrations/connections/${active.id}/sync/`, { config: cfg, auto_assign: auto });
      setActive(data); load();
      toast.success(`Synced: ${data.leads_created} new + ${data.leads_updated} updated leads, ${data.customers_synced} customers`);
    } catch (e) {
      toast.error(e.response?.data?.error || e.response?.data?.detail || "Sync failed");
    } finally { setSyncing(false); }
  };

  if (!list) return <Spinner label="Loading integrations…" />;

  const connected = list.filter((c) => c.status === "connected").length;
  // Only webhook (social) connectors bring real leads. Poll connectors (FXArtha,
  // DAGChain) sync platform users/customers — those don't count as leads.
  const totalLeads = list.reduce((s, c) => s + (c.is_poll ? 0 : c.total_leads), 0);

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Plug className="text-brand-600" /> Integration Hub</h1>
          <p className="text-sm text-ink-400">Connect each business's own Instagram / Google Ads etc. → add its webhook URL on that platform → leads flow straight into that business.</p>
        </div>
        <button className="btn-primary shrink-0" onClick={openAdd}><Plus size={16} /> Add Integration</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="card p-5"><p className="text-3xl font-extrabold text-emerald-600">{connected}</p><p className="text-sm text-ink-400">Connected</p></div>
        <div className="card p-5"><p className="text-3xl font-extrabold text-ink-900">{list.length}</p><p className="text-sm text-ink-400">Integrations</p></div>
        <div className="card p-5"><p className="text-3xl font-extrabold text-brand-600">{totalLeads}</p><p className="text-sm text-ink-400">Leads ingested</p></div>
      </div>

      {list.length === 0 && (
        <div className="card p-10 text-center">
          <p className="text-ink-500 font-semibold">No integrations yet.</p>
          <p className="text-sm text-ink-400 mt-1">Press “Add Integration”, choose a business and platform, and add the webhook URL on that platform.</p>
          <button className="btn-primary mt-4 mx-auto" onClick={openAdd}><Plus size={16} /> Add Integration</button>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {list.map((c) => {
          const { Icon, color } = ICONS[c.platform] || ICONS.website;
          const on = c.status === "connected";
          return (
            <div key={c.id} className="card p-5 flex flex-col">
              <div className="flex items-start justify-between">
                <div className={`grid place-items-center w-12 h-12 rounded-2xl ${color}`}><Icon size={22} /></div>
                {on
                  ? <span className="badge bg-emerald-50 text-emerald-700 flex items-center gap-1"><CheckCircle2 size={12} /> Connected</span>
                  : <span className="badge bg-ink-100 text-ink-500 flex items-center gap-1"><Circle size={12} /> Off</span>}
              </div>
              <h3 className="font-bold text-ink-900 mt-3">{c.label}</h3>
              <p className="text-xs mt-0.5 inline-flex items-center gap-1 text-ink-500">
                <Building2 size={12} /> {c.business_name || "Global (no business)"}
              </p>
              <div className="flex gap-4 mt-3 text-sm">
                <div><span className="font-extrabold text-ink-900">{c.total_leads}</span> <span className="text-ink-400">{c.is_poll ? "users" : "leads"}</span></div>
                <div className="text-ink-400">last: {ago(c.last_lead_at)}</div>
              </div>
              <button className={`mt-4 ${on ? "btn-ghost border border-ink-200" : "btn-primary"}`} onClick={() => open(c)}>
                {on ? "Manage" : "Connect"}
              </button>
            </div>
          );
        })}
      </div>

      {/* add-integration modal */}
      <Modal open={!!adding} onClose={() => setAdding(null)} title="Add integration"
        footer={<>
          <button className="btn-ghost" onClick={() => setAdding(null)}>Cancel</button>
          <button className="btn-primary" onClick={createConn}><Plus size={15} /> Add</button>
        </>}>
        {adding && (
          <div className="space-y-4">
            <div>
              <label className="label">Platform</label>
              <select className="input" value={adding.platform} onChange={(e) => setAdding({ ...adding, platform: e.target.value })}>
                <option value="">Choose a platform…</option>
                {catalogue.map((p) => <option key={p.slug} value={p.slug}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Business</label>
              <select className="input" value={adding.business} onChange={(e) => setAdding({ ...adding, business: e.target.value })}>
                <option value="">Global (not tied to a business)</option>
                {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
              <p className="text-xs text-ink-400 mt-1">Leads from this integration go to this business and are assigned to its RMs.</p>
            </div>
            <div>
              <label className="label">Custom name <span className="text-ink-400 font-normal">(optional)</span></label>
              <input className="input" placeholder="e.g. FX Artha Instagram" value={adding.name} onChange={(e) => setAdding({ ...adding, name: e.target.value })} />
            </div>
          </div>
        )}
      </Modal>

      {/* manage modal */}
      <Modal open={!!active} onClose={() => setActive(null)} title={active ? `${active.label}` : ""}>
        {active && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`badge ${active.status === "connected" ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{active.status}</span>
              <span className="badge bg-brand-50 text-brand-700 inline-flex items-center gap-1"><Building2 size={12} /> {active.business_name || "Global"}</span>
              <span className="text-xs text-ink-400">{active.total_leads} {active.is_poll ? "users synced" : "leads ingested"}</span>
              <button onClick={removeConn} className="ml-auto text-xs text-rose-600 inline-flex items-center gap-1 hover:underline"><Trash2 size={13} /> Delete</button>
            </div>
            <p className="text-xs text-ink-400 -mt-1">Source tag: {active.source_name}</p>

            {/* webhook URL (webhook connectors only) */}
            {active.platform !== "fxartha" && (
              <div>
                <label className="label">Webhook URL (add this in the platform's settings)</label>
                <div className="flex gap-2">
                  <input readOnly value={active.webhook_url} className="input font-mono text-xs" onFocus={(e) => e.target.select()} />
                  <button className="chip !py-2" onClick={() => copy(active.webhook_url)}><Copy size={14} /></button>
                </div>
                <button onClick={regen} className="text-xs text-brand-600 font-semibold mt-1 inline-flex items-center gap-1"><RefreshCw size={12} /> Regenerate secret</button>
              </div>
            )}

            {/* FXArtha poll connector — dashboard snapshot from last sync */}
            {active.platform === "fxartha" && active.config?.dashboard && (
              <div>
                <label className="label">Platform snapshot (last sync)</label>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {[
                    ["Traders", active.config.dashboard.total_traders],
                    ["Active accounts", active.config.dashboard.active_accounts],
                    ["Lots traded", active.config.dashboard.lots_traded],
                    ["Monthly revenue", `$${active.config.dashboard.monthly_revenue}`],
                    ["Deposits", `$${active.config.dashboard.total_deposits}`],
                    ["Withdrawals", `$${active.config.dashboard.total_withdrawals}`],
                  ].map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-ink-50 border border-ink-100 px-3 py-2">
                      <p className="text-xs text-ink-400">{k}</p>
                      <p className="font-bold text-ink-800 tabular-nums">{v}</p>
                    </div>
                  ))}
                </div>
                {active.config.last_sync && <p className="text-xs text-ink-400 mt-1">Last sync: {ago(active.config.last_sync)}</p>}
              </div>
            )}

            {/* config fields */}
            {(active.config_fields || []).length > 0 && (
              <div className="space-y-3">
                <p className="label !mb-0">Credentials (client se mango)</p>
                {active.config_fields.map((f) => (
                  <div key={f}>
                    <label className="label">{f.replace(/_/g, " ")}</label>
                    <input className="input" value={cfg[f] || ""} onChange={(e) => setCfg({ ...cfg, [f]: e.target.value })} placeholder={`Enter ${f}`} />
                  </div>
                ))}
              </div>
            )}

            {/* auto assign */}
            <label className="flex items-center gap-3 p-3 rounded-xl bg-ink-50 border border-ink-100 cursor-pointer">
              <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
              <div><p className="text-sm font-semibold text-ink-800">Auto-assign new leads</p><p className="text-xs text-ink-400">Aate hi RM ko (load-balanced) assign + notify</p></div>
            </label>

            {/* recent logs */}
            {active.recent_logs?.length > 0 && (
              <div>
                <p className="label">Recent activity</p>
                <div className="space-y-1 max-h-28 overflow-y-auto">
                  {active.recent_logs.map((l) => (
                    <div key={l.id} className="flex items-center gap-2 text-xs">
                      <span className={`w-2 h-2 rounded-full ${l.status === "success" ? "bg-emerald-500" : "bg-amber-500"}`} />
                      <span className="text-ink-600">{l.message}</span>
                      <span className="text-ink-400 ml-auto">{ago(l.created_at)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              {active.platform === "fxartha" ? (
                <>
                  <button className="btn-primary flex-1 disabled:opacity-50" onClick={sync} disabled={syncing}>
                    <RefreshCcw size={15} className={syncing ? "animate-spin" : ""} /> {syncing ? "Syncing…" : "Sync now"}
                  </button>
                  {active.status === "connected" && <button className="btn-danger" onClick={disconnect}>Disconnect</button>}
                </>
              ) : active.status === "connected" ? (
                <>
                  <button className="btn-primary flex-1" onClick={connect}>Save</button>
                  <button className="btn bg-amber-50 text-amber-700 hover:bg-amber-100" onClick={sendTest}><Zap size={15} /> Send Test Lead</button>
                  <button className="btn-danger" onClick={disconnect}>Disconnect</button>
                </>
              ) : (
                <button className="btn-primary flex-1" onClick={connect}><Plug size={15} /> Connect</button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
