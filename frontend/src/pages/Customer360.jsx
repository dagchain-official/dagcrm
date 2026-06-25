import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Mail, Phone, MapPin, DollarSign, Package, LifeBuoy,
  MessageSquare, Calendar, Ticket as TicketIcon, Activity, UserPlus, Clock,
  Plus, Upload, FileText, Download, Paperclip, FileSignature,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState, Modal } from "../components/ui";
import DataForm from "../components/DataForm";
import ProposalBuilder, { blankProposal } from "../components/ProposalBuilder";
import { STATUS_COLORS } from "../config/resources";
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
  const [d, setD] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [err, setErr] = useState(false);
  const [qa, setQa] = useState(null); // quick-action key
  const [saving, setSaving] = useState(false);
  const [proposal, setProposal] = useState(null);

  const load = () => api.get(`/customers/${id}/overview/`).then((r) => setD(r.data)).catch(() => { if (!d) setErr(true); });
  usePolling(load, 2000, [id]);   // live refresh; re-fetches immediately when id changes

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
            <h1 className="text-2xl font-extrabold text-ink-900">{c.name}</h1>
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-sm text-ink-500">
              {c.email && <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {c.email}</span>}
              {c.phone && <span className="inline-flex items-center gap-1.5"><Phone size={14} /> {c.phone}</span>}
              {c.country && <span className="inline-flex items-center gap-1.5"><MapPin size={14} /> {c.country}</span>}
              <span className="inline-flex items-center gap-1.5"><Calendar size={14} /> Customer since {date(c.created_at)}</span>
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
        <button className="chip" onClick={() => setProposal({ ...blankProposal(), contactType: "customer", customer: id, title: `Proposal for ${c.name}` })}><FileSignature size={15} /> Create Proposal</button>
        <label className="chip cursor-pointer">
          <Upload size={15} /> Upload File
          <input type="file" className="hidden" onChange={upload} />
        </label>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Kpi icon={DollarSign} label="Net Revenue" value={money(k.total_net_revenue)} tint="bg-emerald-100 text-emerald-600" />
        <Kpi icon={Package} label="Products" value={k.products_count} tint="bg-brand-100 text-brand-600" />
        <Kpi icon={LifeBuoy} label="Open Tickets" value={k.open_tickets} tint="bg-amber-100 text-amber-600" />
        <Kpi icon={MessageSquare} label="Communications" value={k.communications_count} tint="bg-blue-100 text-blue-600" />
      </div>

      {/* tabs */}
      <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-full sm:w-fit overflow-x-auto">
        {TABS.map((t) => (
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

      {/* PRODUCTS */}
      {tab === "Products" && (
        <Section>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
              <Th>Product</Th><Th>Business</Th><Th>Status</Th>
            </tr></thead>
            <tbody>
              {d.products.map((p) => (
                <tr key={p.id} className="border-t border-ink-100">
                  <td className="py-3 px-4 font-medium text-ink-800">{p.product_name || "—"}</td>
                  <td className="py-3 px-4 text-ink-500">{p.business_name}</td>
                  <td className="py-3 px-4"><Badge value={p.status} map={STATUS_COLORS} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {d.products.length === 0 && <EmptyState title="No products" />}
        </Section>
      )}

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

      {proposal && (
        <ProposalBuilder initial={proposal} onClose={() => setProposal(null)}
          onSaved={() => { setProposal(null); load(); }} />
      )}
    </div>
  );
}
