import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Mail, Phone, MapPin, DollarSign, Package, LifeBuoy,
  MessageSquare, Calendar, Ticket as TicketIcon, Activity, UserPlus, Clock,
  Plus, Upload, FileText, Download, Paperclip, UserCog,
  CandlestickChart, ArrowDownToLine, ArrowUpFromLine, Wallet, Coins, TrendingDown,
  ShoppingBag, Boxes,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState, Modal } from "../components/ui";
import DataForm from "../components/DataForm";
import { STATUS_COLORS } from "../config/resources";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

const sel = (...o) => o.map((x) => ({ value: x, label: x[0].toUpperCase() + x.slice(1).replace("_", " ") }));

// quick-action form configs (customer auto-attached on submit)
const QUICK = {
  communication: {
    title: "Add Communication", endpoint: "communications",
    fields: [
      { key: "channel", label: "Channel", type: "select", options: sel("whatsapp", "email", "sms", "telegram") },
      { key: "direction", label: "Direction", type: "select", options: sel("outbound", "inbound") },
      { key: "message", label: "Message", type: "textarea" },
    ],
  },
  ticket: {
    title: "New Ticket", endpoint: "tickets",
    fields: [
      { key: "ticket_no", label: "Ticket no", required: true },
      { key: "category", label: "Category" },
      { key: "priority", label: "Priority", type: "select", options: sel("low", "medium", "high", "urgent") },
      { key: "status", label: "Status", type: "select", options: sel("open", "assigned", "in_progress", "resolved", "closed") },
    ],
  },
  revenue: {
    title: "Add Revenue", endpoint: "revenues",
    fields: [
      { key: "business", label: "Business", type: "ref", ref: "businesses", labelKey: "name" },
      { key: "product", label: "Product", type: "ref", ref: "products", labelKey: "name" },
      { key: "gross_revenue", label: "Gross revenue", type: "number", required: true },
      { key: "commission", label: "Commission", type: "number" },
    ],
  },
};

const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const dt = (v) => (v ? new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");

const TABS = ["Overview", "Products", "Revenue", "Tickets", "Communications", "Documents", "Timeline"];

const PLATFORM_BADGE = {
  "FX Artha": "bg-sky-50 text-sky-700 ring-1 ring-sky-200",
  DAGChain: "bg-violet-50 text-violet-700 ring-1 ring-violet-200",
};

const EVENT_ICON = {
  revenue: { icon: DollarSign, tint: "bg-emerald-100 text-emerald-600" },
  ticket: { icon: TicketIcon, tint: "bg-amber-100 text-amber-600" },
  communication: { icon: MessageSquare, tint: "bg-blue-100 text-blue-600" },
  activity: { icon: Activity, tint: "bg-violet-100 text-violet-600" },
};

function Kpi({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-5">
      <div className={`grid place-items-center w-11 h-11 rounded-2xl ${tint}`}><Icon size={20} /></div>
      <p className="text-2xl font-extrabold text-ink-900 mt-4 tabular-nums">{value}</p>
      <p className="text-sm text-ink-400 mt-0.5">{label}</p>
    </div>
  );
}

function Section({ children }) {
  return <div className="card p-5">{children}</div>;
}

function Th({ children, right }) {
  return <th className={`pb-3 px-4 font-semibold ${right ? "text-right" : ""}`}>{children}</th>;
}

export default function Customer360() {
  const { id } = useParams();
  const toast = useToast();
  const { user } = useAuth();
  const [d, setD] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [err, setErr] = useState(false);
  const [qa, setQa] = useState(null); // quick-action key
  const [saving, setSaving] = useState(false);
  const [reassign, setReassign] = useState(false);   // reassign modal open
  const [assignables, setAssignables] = useState([]);
  const [newOwner, setNewOwner] = useState("");
  const [editSale, setEditSale] = useState(null);   // null=closed, {}=new, {...}=edit

  const load = () => api.get(`/customers/${id}/overview/`).then((r) => setD(r.data)).catch(() => { if (!d) setErr(true); });
  usePolling(load, 2000, [id]);   // live refresh; re-fetches immediately when id changes

  const openReassign = () => {
    setNewOwner("");
    setReassign(true);
    api.get("/users/assignable/").then((r) => setAssignables(r.data)).catch(() => setAssignables([]));
  };
  const submitReassign = async () => {
    if (!newOwner) return toast.error("Please select an employee");
    setSaving(true);
    try {
      const { data } = await api.post(`/customers/${id}/reassign/`, { user: newOwner });
      setReassign(false);
      load();
      toast.success(`Customer is now assigned to ${data.assigned_name}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Reassign failed");
    } finally {
      setSaving(false);
    }
  };

  const submitQuick = async (form) => {
    setSaving(true);
    const payload = { ...form, customer: Number(id) };
    Object.keys(payload).forEach((k) => payload[k] === "" && delete payload[k]);
    try {
      await api.post(`/${QUICK[qa].endpoint}/`, payload);
      setQa(null);
      load();
      toast.success(`${QUICK[qa].title.replace("Add ", "").replace("New ", "")} added`);
    } catch (e) {
      toast.error("Save failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const saveSale = async (form) => {
    setSaving(true);
    try {
      if (form.id) await api.patch(`/post-sales/${form.id}/`, form);
      else await api.post("/post-sales/", { ...form, customer: Number(id) });
      setEditSale(null);
      load();
      toast.success("Sale saved");
    } catch (e) {
      toast.error("Save failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("customer", id);
    await api.post("/attachments/", fd, { headers: { "Content-Type": "multipart/form-data" } });
    e.target.value = "";
    load();
    toast.success("File uploaded");
  };

  if (err) return <EmptyState title="Customer not found" hint="It may have been deleted." />;
  if (!d) return <Spinner label="Loading customer 360…" />;

  const c = d.customer;
  const k = d.kpis;
  const tr = d.trading || {};
  const num = (v) => Number(v || 0).toLocaleString();
  const purchases = d.purchases || [];
  const sales = d.sales || [];
  const visibleTabs = (() => {
    const t = [...TABS];                       // Overview, Products, Revenue, …
    let at = 1;
    if (purchases.length) t.splice(at++, 0, "Purchases");
    t.splice(at, 0, "Sales");                   // always available (can add manually)
    return t;
  })();

  const Timeline = ({ items }) => (
    <div className="space-y-1">
      {items.length === 0 && <EmptyState title="No activity yet" />}
      {items.map((e, i) => {
        const cfg = EVENT_ICON[e.type] || EVENT_ICON.activity;
        return (
          <div key={i} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`grid place-items-center w-9 h-9 rounded-xl ${cfg.tint} shrink-0`}>
                <cfg.icon size={16} />
              </div>
              {i < items.length - 1 && <div className="w-px flex-1 bg-ink-200 my-1" />}
            </div>
            <div className="pb-5 min-w-0">
              <p className="text-sm font-semibold text-ink-800">{e.title}</p>
              <p className="text-xs text-ink-500 truncate">{e.detail}</p>
              <p className="text-[11px] text-ink-400 mt-0.5">{dt(e.date)}</p>
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="space-y-5">
      <Link to="/m/customers" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
        <ArrowLeft size={16} /> Back to Customers
      </Link>

      {/* header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="grid place-items-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white text-2xl font-extrabold shrink-0">
            {c.name?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-extrabold text-ink-900">{c.name}</h1>
              {d.platform && (
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${PLATFORM_BADGE[d.platform] || "bg-ink-100 text-ink-600"}`}>
                  {d.platform} account
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-sm text-ink-500">
              {c.email && <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {c.email}</span>}
              {c.phone && <span className="inline-flex items-center gap-1.5"><Phone size={14} /> {c.phone}</span>}
              {c.country && <span className="inline-flex items-center gap-1.5"><MapPin size={14} /> {c.country}</span>}
              <span className="inline-flex items-center gap-1.5"><Calendar size={14} /> Customer since {date(c.created_at)}</span>
              <span className="inline-flex items-center gap-1.5"><UserCog size={14} /> RM: <b className="text-ink-700">{c.assigned_name || "Unassigned"}</b></span>
            </div>
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs text-ink-400 uppercase tracking-wide">Lifetime Value</p>
            <p className="text-2xl font-extrabold text-emerald-600 tabular-nums">{money(k.total_net_revenue)}</p>
          </div>
        </div>
      </div>

      {/* quick actions */}
      <div className="flex flex-wrap gap-2">
        <button className="chip" onClick={() => setQa("communication")}><MessageSquare size={15} /> Add Communication</button>
        <button className="chip" onClick={() => setQa("ticket")}><TicketIcon size={15} /> New Ticket</button>
        <button className="chip" onClick={() => setQa("revenue")}><DollarSign size={15} /> Add Revenue</button>
        <label className="chip cursor-pointer">
          <Upload size={15} /> Upload File
          <input type="file" className="hidden" onChange={upload} />
        </label>
        {user?.can_assign_leads && (
          <button className="chip" onClick={openReassign}><UserCog size={15} /> Reassign RM</button>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={DollarSign} label="Net Revenue" value={money(k.total_net_revenue)} tint="bg-emerald-100 text-emerald-600" />
        <Kpi icon={Package} label="Products" value={(k.products_count || 0) + (d.platforms?.length || 0)} tint="bg-brand-100 text-brand-600" />
        <Kpi icon={LifeBuoy} label="Open Tickets" value={k.open_tickets} tint="bg-amber-100 text-amber-600" />
        <Kpi icon={MessageSquare} label="Communications" value={k.communications_count} tint="bg-blue-100 text-blue-600" />
      </div>

      {/* Trading activity across BOTH platforms — filter FX Artha / DAGChain */}
      {d.platforms?.length > 0 && <PlatformActivity platforms={d.platforms} />}

      {/* tabs */}
      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-full sm:w-fit overflow-x-auto">
        {visibleTabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition
              ${tab === t ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {/* OVERVIEW */}
      {tab === "Overview" && (
        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-5">
            <Section>
              <h3 className="font-bold text-ink-900 mb-4">Recent Activity</h3>
              <Timeline items={d.timeline.slice(0, 6)} />
            </Section>
          </div>
          <div className="space-y-5">
            <Section>
              <h3 className="font-bold text-ink-900 mb-3">Origin Lead</h3>
              {d.origin_lead ? (
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-ink-50">
                  <div className="grid place-items-center w-9 h-9 rounded-xl bg-violet-100 text-violet-600"><UserPlus size={16} /></div>
                  <div>
                    <p className="text-sm font-semibold text-ink-800">{d.origin_lead.lead_code} · {d.origin_lead.name}</p>
                    <p className="text-xs text-ink-400">Source: {d.origin_lead.source_name || "—"}</p>
                  </div>
                </div>
              ) : <p className="text-sm text-ink-400">No originating lead linked.</p>}
            </Section>
            <Section>
              <h3 className="font-bold text-ink-900 mb-3">Products ({d.products.length})</h3>
              <div className="space-y-2">
                {d.products.map((p) => (
                  <div key={p.id} className="flex items-center justify-between p-2.5 rounded-xl bg-ink-50">
                    <span className="text-sm text-ink-700">{p.product_name || p.business_name}</span>
                    <Badge value={p.status} map={STATUS_COLORS} />
                  </div>
                ))}
                {d.products.length === 0 && <p className="text-sm text-ink-400">No products.</p>}
              </div>
            </Section>
          </div>
        </div>
      )}

      {/* PLATFORM PURCHASES — what the client actually bought on FX Artha / DAGChain */}
      {tab === "Purchases" && (
        <Section>
          <div className="flex items-center gap-2 mb-4">
            <ShoppingBag size={18} className="text-brand-600" />
            <h3 className="font-bold text-ink-900">Platform Purchases</h3>
            {d.platform && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${PLATFORM_BADGE[d.platform] || "bg-ink-100 text-ink-600"}`}>{d.platform}</span>
            )}
          </div>
          <p className="text-xs text-ink-400 mb-4">
            Matched to this customer from their {d.platform} login. Every new purchase is added automatically as the platform syncs.
          </p>
          <div className="space-y-3">
            {purchases.map((p, i) => (
              <div key={i} className="flex items-center justify-between gap-3 p-4 rounded-2xl bg-ink-50">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="grid place-items-center w-10 h-10 rounded-xl bg-brand-100 text-brand-600 shrink-0">
                    <Boxes size={18} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-ink-800 truncate">{p.product}</p>
                    <p className="text-xs text-ink-400">
                      {p.platform}{p.date ? ` · ${date(p.date)}` : ""}
                      {p.kind === "fx" && p.lots ? ` · ${num(p.lots)} lots` : ""}
                      {p.kind === "node" && p.rewards ? ` · ${money(p.rewards)} rewards` : ""}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-lg font-extrabold text-ink-900 tabular-nums">{money(p.price)}</p>
                  {p.kind === "fx"
                    ? <p className="text-[11px] text-emerald-600 font-semibold">{money(p.brokerage)} brokerage</p>
                    : <Badge value={p.status} map={STATUS_COLORS} />}
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between mt-5 pt-4 border-t border-ink-100">
            <span className="text-sm font-semibold text-ink-500">
              {d.platform === "FX Artha" ? "Total deposit" : "Total purchased"}
            </span>
            <span className="text-xl font-extrabold text-ink-900 tabular-nums">
              {money(purchases.reduce((s, p) => s + Number(p.price || 0), 0))}
            </span>
          </div>
        </Section>
      )}

      {/* SALES & POST-SALES — onboarding, service, renewal, top-up, health */}
      {tab === "Sales" && (
        <Section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-ink-900 flex items-center gap-2"><ShoppingBag size={18} className="text-brand-600" /> Sales &amp; Onboarding <span className="text-sm font-normal text-ink-400">({sales.length})</span></h3>
            <button onClick={() => setEditSale({})} className="btn-primary !py-2 !px-4 text-sm inline-flex items-center gap-1.5"><Plus size={15} /> Add sale</button>
          </div>
          {sales.length === 0 && <EmptyState title="No sales yet" hint="A sale is created automatically when a lead converts, or add one here." />}
          <div className="space-y-3">
            {sales.map((s) => (
              <div key={s.id} className="rounded-2xl border border-ink-100 p-4">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <span className="font-bold text-ink-900">{s.product_name || "Sale"}</span>
                  <Badge value={s.sale_type} map={STATUS_COLORS} />
                  <Badge value={s.sale_status} map={STATUS_COLORS} />
                  <span className="ml-auto flex items-center gap-2">
                    <span className="text-xs text-ink-400">Health</span>
                    <Badge value={s.post_sales_health} map={STATUS_COLORS} />
                    <button onClick={() => setEditSale(s)} className="chip !py-1.5 text-xs">Edit</button>
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-y-2 gap-x-4 text-sm">
                  {[
                    ["Close date", date(s.close_date)],
                    ["Gross value", money(s.gross_value)],
                    ["Collected", money(s.collected_value)],
                    ["Commission", money(s.commission)],
                    ["Gross profit", money(s.gross_profit)],
                    ["Agent", s.agent_name || "—"],
                    ["Onboarding owner", s.onboarding_owner_name || "—"],
                    ["Delivery", date(s.delivery_date)],
                    ["Next renewal", date(s.next_renewal_date)],
                  ].map(([k, v]) => (
                    <div key={k}><p className="text-[11px] text-ink-400 uppercase tracking-wide">{k}</p><p className="font-semibold text-ink-800">{v}</p></div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  <Chip on={s.welcome_call === "done"} label={`Welcome call: ${s.welcome_call}`} />
                  <Chip on={s.documents_complete} label={`Documents: ${s.documents_complete ? "complete" : "pending"}`} />
                  <Chip on={s.service_status === "active"} label={`Service: ${s.service_status}`} />
                  {s.topup_opportunity && <Chip on label={`Top-up: ${money(s.topup_value)}`} />}
                  {s.referral_received && <Chip on label="Referral received" />}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* PRODUCTS */}
      {tab === "Products" && (() => {
        // the platform account(s) they opened count as products too
        const platRows = (d.platforms || []).map((p) => ({
          id: `plat-${p.platform}`,
          product_name: p.platform === "DAGChain"
            ? (p.stats.account_type || "DAGChain Account")
            : `${p.stats.account_type || "FX Artha"} Account`,
          business_name: p.platform,
          status: "active",
        }));
        const rows = [...platRows, ...d.products];
        return (
          <Section>
            <table className="w-full text-sm">
              <thead><tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                <Th>Product</Th><Th>Business</Th><Th>Status</Th>
              </tr></thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.id} className="border-t border-ink-100">
                    <td className="py-3 px-4 font-medium text-ink-800">{p.product_name || "—"}</td>
                    <td className="py-3 px-4 text-ink-500">{p.business_name}</td>
                    <td className="py-3 px-4"><Badge value={p.status} map={STATUS_COLORS} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length === 0 && <EmptyState title="No products" />}
          </Section>
        );
      })()}

      {/* REVENUE */}
      {tab === "Revenue" && (
        <Section>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
              <Th>Business</Th><Th right>Gross</Th><Th right>Commission</Th><Th right>Net</Th><Th>Date</Th>
            </tr></thead>
            <tbody>
              {d.revenues.map((r) => (
                <tr key={r.id} className="border-t border-ink-100">
                  <td className="py-3 px-4 font-medium text-ink-800">{r.business_name || "—"}</td>
                  <td className="py-3 px-4 text-right tabular-nums">{money(r.gross_revenue)}</td>
                  <td className="py-3 px-4 text-right tabular-nums text-ink-500">{money(r.commission)}</td>
                  <td className="py-3 px-4 text-right tabular-nums font-semibold text-emerald-600">{money(r.net_revenue)}</td>
                  <td className="py-3 px-4 text-ink-500">{date(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {d.revenues.length === 0 && <EmptyState title="No revenue recorded" />}
        </Section>
      )}

      {/* TICKETS */}
      {tab === "Tickets" && (
        <Section>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
              <Th>Ticket</Th><Th>Category</Th><Th>Priority</Th><Th>Status</Th>
            </tr></thead>
            <tbody>
              {d.tickets.map((t) => (
                <tr key={t.id} className="border-t border-ink-100">
                  <td className="py-3 px-4 font-medium text-ink-800">{t.ticket_no}</td>
                  <td className="py-3 px-4 text-ink-500">{t.category || "—"}</td>
                  <td className="py-3 px-4"><Badge value={t.priority} map={STATUS_COLORS} /></td>
                  <td className="py-3 px-4"><Badge value={t.status} map={STATUS_COLORS} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {d.tickets.length === 0 && <EmptyState title="No tickets" />}
        </Section>
      )}

      {/* COMMUNICATIONS */}
      {tab === "Communications" && (
        <Section>
          <div className="space-y-2">
            {d.communications.map((cm) => (
              <div key={cm.id} className="flex items-start gap-3 p-3 rounded-2xl bg-ink-50">
                <div className="grid place-items-center w-9 h-9 rounded-xl bg-blue-100 text-blue-600 shrink-0"><MessageSquare size={16} /></div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-ink-800 capitalize">{cm.channel} · {cm.direction}</p>
                  <p className="text-xs text-ink-500">{cm.message}</p>
                </div>
                <span className="text-[11px] text-ink-400 shrink-0">{dt(cm.created_at)}</span>
              </div>
            ))}
            {d.communications.length === 0 && <EmptyState title="No communications" />}
          </div>
        </Section>
      )}

      {/* DOCUMENTS */}
      {tab === "Documents" && (
        <Section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-ink-900 flex items-center gap-2"><Paperclip size={18} className="text-brand-600" /> Documents</h3>
            <label className="btn-primary cursor-pointer text-sm">
              <Upload size={15} /> Upload
              <input type="file" className="hidden" onChange={upload} />
            </label>
          </div>
          <div className="space-y-2">
            {(d.attachments || []).map((a) => (
              <div key={a.id} className="flex items-center gap-3 p-3 rounded-2xl bg-ink-50">
                <div className="grid place-items-center w-9 h-9 rounded-xl bg-brand-100 text-brand-600 shrink-0"><FileText size={16} /></div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-ink-800 truncate">{a.name}</p>
                  <p className="text-[11px] text-ink-400">{a.uploaded_by_name || "—"} · {dt(a.created_at)}</p>
                </div>
                <a href={a.file_url} target="_blank" rel="noreferrer" className="btn-ghost p-2 text-brand-600"><Download size={16} /></a>
              </div>
            ))}
            {(!d.attachments || d.attachments.length === 0) && <EmptyState title="No documents" hint="Upload files for this customer." />}
          </div>
        </Section>
      )}

      {/* TIMELINE */}
      {tab === "Timeline" && (
        <Section>
          <div className="flex items-center gap-2 mb-4 text-ink-900 font-bold">
            <Clock size={18} className="text-brand-600" /> Full Timeline
          </div>
          <Timeline items={d.timeline} />
        </Section>
      )}

      {/* quick-action modal */}
      <Modal open={!!qa} onClose={() => setQa(null)} title={qa ? QUICK[qa].title : ""}>
        {qa && (
          <DataForm
            fields={QUICK[qa].fields}
            initial={Object.fromEntries(QUICK[qa].fields.map((f) => [f.key, ""]))}
            submitting={saving}
            onSubmit={submitQuick}
            onCancel={() => setQa(null)}
          />
        )}
      </Modal>

      {/* reassign RM modal */}
      <Modal open={reassign} onClose={() => setReassign(null)} title="Reassign to another employee"
        footer={<>
          <button className="btn-ghost" onClick={() => setReassign(false)}>Cancel</button>
          <button className="btn-primary" disabled={saving} onClick={submitReassign}><UserCog size={15} /> Reassign</button>
        </>}>
        <div className="space-y-3">
          <p className="text-sm text-ink-500">Abhi RM: <b className="text-ink-800">{c.assigned_name || "Unassigned"}</b></p>
          <div>
            <label className="label">Naya RM</label>
            <select className="input" value={newOwner} onChange={(e) => setNewOwner(e.target.value)}>
              <option value="">Select an employee…</option>
              {assignables.map((u) => <option key={u.id} value={u.id}>{u.name} — {u.role_name}</option>)}
            </select>
          </div>
          <p className="text-xs text-ink-400">
            Future revenue, AUM and KPIs will go to the new RM. Past records (already logged) stay with the previous RM.
          </p>
        </div>
      </Modal>

      {/* SALE / ONBOARDING editor */}
      <Modal open={!!editSale} onClose={() => setEditSale(null)}
        title={editSale?.id ? "Edit sale & onboarding" : "Add sale"}>
        {editSale && <PostSaleEditor sale={editSale} saving={saving}
          onSave={saveSale} onCancel={() => setEditSale(null)} />}
      </Modal>
    </div>
  );
}

// a small status pill for the onboarding checklist
function Chip({ on, label }) {
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${on ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>
      {label}
    </span>
  );
}

// Trading activity for a customer who may hold FX Artha AND DAGChain accounts —
// one place, a filter to switch platforms.
function PlatformActivity({ platforms }) {
  const [i, setI] = useState(0);
  const p = platforms[i] || platforms[0];
  const s = p.stats || {};
  const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  const FX = [
    ["Balance", money(s.balance), "text-teal-600", Wallet],
    ["Lots Traded", num(s.lots_traded), "text-brand-600", CandlestickChart],
    ["Deposits", money(s.deposits), "text-emerald-600", ArrowDownToLine],
    ["Withdrawals", money(s.withdrawals), "text-rose-500", ArrowUpFromLine],
    ["Net AUM", money(s.net_aum), "text-ink-500", Wallet],
    ["Gross Brokerage", money(s.gross_brokerage), "text-violet-600", DollarSign],
    ["IB Commission", money(s.ib_commission), "text-sky-600", Coins],
    ["Trading Loss", money(s.trading_loss), "text-amber-600", TrendingDown],
  ];
  const DAG = [
    ["Nodes", num(s.nodes), "text-brand-600", Boxes],
    ["Paid Nodes", num(s.nodes_paid), "text-emerald-600", Boxes],
    ["Node Value", money(s.node_value), "text-violet-600", DollarSign],
    ["Rewards", money(s.rewards), "text-amber-600", Coins],
    ["DGC Balance", num(s.dgc_balance), "text-sky-600", Wallet],
    ["Staked", num(s.staked), "text-teal-600", Coins],
  ];
  const tiles = p.platform === "DAGChain" ? DAG : FX;
  return (
    <div className="card p-5">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h3 className="font-bold text-ink-900 flex items-center gap-2">
          <CandlestickChart size={18} className="text-brand-600" /> Trading Activity
        </h3>
        {platforms.length > 1 ? (
          <div className="flex gap-1 p-1 bg-ink-100 rounded-xl">
            {platforms.map((pp, idx) => (
              <button key={pp.platform} onClick={() => setI(idx)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${i === idx ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
                {pp.platform}
              </button>
            ))}
          </div>
        ) : <span className="text-xs font-normal text-ink-400">({p.platform})</span>}
      </div>
      <p className="text-sm text-ink-500 mb-4">
        <b className="text-ink-700">Account:</b> {s.account_type || "—"}
        {s.account_number ? ` · #${s.account_number}` : ""}
        {" · "}<b className="text-ink-700">Balance:</b> {p.platform === "DAGChain" ? `${num(s.balance)} DGC` : money(s.balance)}
      </p>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {tiles.map(([label, val, color, Icon]) => (
          <div key={label} className="rounded-2xl bg-ink-500/10 border border-ink-500/20 p-4">
            <div className={`flex items-center gap-2 ${color}`}><Icon size={16} /><span className="text-xs font-semibold uppercase tracking-wide">{label}</span></div>
            <p className="text-2xl font-extrabold text-ink-900 mt-2 tabular-nums">{val}</p>
          </div>
        ))}
      </div>
      {p.platform !== "DAGChain" && s.symbol_lots?.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-2">Lots by instrument</p>
          <div className="flex flex-wrap gap-2">
            {s.symbol_lots.map((it) => (
              <div key={it.symbol} className="rounded-xl bg-ink-500/10 border border-ink-500/20 px-3 py-2">
                <span className="text-sm font-bold text-ink-900">{it.symbol}</span>
                <span className="text-sm text-ink-600 ml-2 tabular-nums">{num(it.lots)} lots</span>
                {it.brokerage > 0 && <span className="text-xs text-ink-400 ml-2 tabular-nums">· {money(it.brokerage)} brok.</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const SALE_SELECTS = {
  sale_type: ["new", "renewal", "topup"],
  sale_status: ["closed_won", "pending", "cancelled"],
  welcome_call: ["pending", "done"],
  service_status: ["active", "paused", "churned"],
  post_sales_health: ["healthy", "at_risk", "churned"],
};
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1).replace(/_/g, " ") : "");

// field helpers are module-level so they don't remount (and lose focus) on keystroke
const FNum = ({ f, set, k, label }) => (
  <div><label className="label">{label}</label>
    <input className="input" type="number" step="0.01" value={f[k] ?? ""} onChange={(e) => set(k, e.target.value)} /></div>
);
const FSel = ({ f, set, k, label }) => (
  <div><label className="label">{label}</label>
    <select className="input" value={f[k] || ""} onChange={(e) => set(k, e.target.value)}>
      {SALE_SELECTS[k].map((o) => <option key={o} value={o}>{cap(o)}</option>)}
    </select></div>
);
const FDt = ({ f, set, k, label }) => (
  <div><label className="label">{label}</label>
    <input className="input" type="date" value={(f[k] || "").slice(0, 10)} onChange={(e) => set(k, e.target.value || null)} /></div>
);
const FBool = ({ f, set, k, label }) => (
  <label className="flex items-center gap-2 text-sm text-ink-700 cursor-pointer py-1">
    <input type="checkbox" checked={!!f[k]} onChange={(e) => set(k, e.target.checked)} /> {label}
  </label>
);

function PostSaleEditor({ sale, onSave, onCancel, saving }) {
  const [f, setF] = useState({
    sale_type: "new", sale_status: "closed_won", welcome_call: "pending",
    service_status: "active", post_sales_health: "healthy",
    gross_value: 0, collected_value: 0, commission: 0, direct_cost: 0, topup_value: 0,
    documents_complete: false, topup_opportunity: false, referral_received: false,
    ...sale,
  });
  const [people, setPeople] = useState([]);
  const [products, setProducts] = useState([]);
  useEffect(() => {
    api.get("/users/assignable/").then((r) => setPeople(r.data)).catch(() => setPeople([]));
    api.get("/products/").then((r) => setProducts(r.data.results || r.data || [])).catch(() => setProducts([]));
  }, []);
  const set = (k, v) => setF((o) => ({ ...o, [k]: v }));
  const p = { f, set };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <FSel {...p} k="sale_type" label="Sale type" />
        <FSel {...p} k="sale_status" label="Sale status" />
        <div className="col-span-2"><label className="label">Product</label>
          <select className="input" value={f.product || ""} onChange={(e) => set("product", e.target.value || null)}>
            <option value="">—</option>
            {products.map((pr) => <option key={pr.id} value={pr.id}>{pr.name}</option>)}
          </select></div>
        <FNum {...p} k="gross_value" label="Gross value ($)" />
        <FNum {...p} k="collected_value" label="Collected ($)" />
        <FNum {...p} k="commission" label="Revenue / commission ($)" />
        <FNum {...p} k="direct_cost" label="Direct cost ($)" />
        <FDt {...p} k="close_date" label="Close date" />
        <FDt {...p} k="delivery_date" label="Delivery date" />
      </div>

      <div className="border-t border-ink-100 pt-3">
        <p className="text-xs font-bold text-ink-500 uppercase tracking-wide mb-2">Onboarding &amp; service</p>
        <div className="grid grid-cols-2 gap-3">
          <FSel {...p} k="welcome_call" label="Welcome call" />
          <FSel {...p} k="service_status" label="Service status" />
          <FDt {...p} k="next_renewal_date" label="Next renewal" />
          <div><label className="label">Onboarding owner</label>
            <select className="input" value={f.onboarding_owner || ""} onChange={(e) => set("onboarding_owner", e.target.value || null)}>
              <option value="">—</option>
              {people.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select></div>
          <FSel {...p} k="post_sales_health" label="Post-sales health" />
        </div>
        <div className="flex flex-wrap gap-x-5 mt-2">
          <FBool {...p} k="documents_complete" label="Documents complete" />
          <FBool {...p} k="topup_opportunity" label="Top-up opportunity" />
          <FBool {...p} k="referral_received" label="Referral received" />
        </div>
        {f.topup_opportunity && <div className="mt-1 w-40"><FNum {...p} k="topup_value" label="Top-up value ($)" /></div>}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button className="btn-primary" disabled={saving} onClick={() => onSave(f)}>Save</button>
      </div>
    </div>
  );
}
