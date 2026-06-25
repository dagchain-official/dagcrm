import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Phone, MessageCircle, Mail, FileText, Mic, StickyNote,
  Calendar, MapPin, Target as TargetIcon, Clock, Send,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState, Modal, ScorePill } from "../components/ui";
import ProposalBuilder, { blankProposal } from "../components/ProposalBuilder";
import { STATUS_COLORS } from "../config/resources";
import { useToast } from "../context/ToastContext";

const dt = (v) => (v ? new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");

const ACT_ICON = {
  call: { icon: Phone, tint: "bg-emerald-100 text-emerald-600" },
  whatsapp: { icon: MessageCircle, tint: "bg-green-100 text-green-600" },
  email: { icon: Mail, tint: "bg-blue-100 text-blue-600" },
  proposal: { icon: FileText, tint: "bg-violet-100 text-violet-600" },
  meeting: { icon: Calendar, tint: "bg-amber-100 text-amber-600" },
  note: { icon: StickyNote, tint: "bg-ink-100 text-ink-500" },
};

// funnel order for the progress strip
const FUNNEL = ["new", "contacted", "qualified", "converted"];

export default function LeadDetail() {
  const { id } = useParams();
  const toast = useToast();
  const [d, setD] = useState(null);
  const [err, setErr] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msgModal, setMsgModal] = useState(null); // {type}
  const [msg, setMsg] = useState("");
  const [proposal, setProposal] = useState(null);

  const load = () => api.get(`/leads/${id}/overview/`).then((r) => setD(r.data)).catch(() => { if (!d) setErr(true); });
  usePolling(load, 2000, [id]);   // live refresh; re-fetches immediately when id changes

  const engage = async (type, message = "") => {
    setBusy(true);
    try {
      const prev = d.lead.status;
      const { data } = await api.post(`/leads/${id}/engage/`, { type, message });
      await load();
      const t = data.telephony;
      const liveNote = t?.live ? " (live via Twilio)" : t?.note ? ` — ${t.note}` : "";
      toast.success(`${type === "call" ? "Call placed" : type === "whatsapp" ? "WhatsApp sent" : type === "email" ? "Email sent" : "Proposal sent"}${liveNote}`);
      if (data.lead.status !== prev) toast.info(`Status auto-advanced: ${prev} → ${data.lead.status}`);
    } catch (e) {
      toast.error("Action failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setBusy(false);
      setMsgModal(null);
      setMsg("");
    }
  };

  if (err) return <EmptyState title="Lead not found" />;
  if (!d) return <Spinner label="Loading lead…" />;
  const l = d.lead;
  const rank = FUNNEL.indexOf(l.status);

  const onAction = (type) => {
    if (type === "proposal") return setProposal({ ...blankProposal(), contactType: "lead", lead: id, title: `Proposal for ${l.name}` });
    if (type === "whatsapp" || type === "email") return setMsgModal({ type });
    engage(type);
  };
  const ActionBtn = ({ type, icon: Icon, label, cls }) => (
    <button disabled={busy} onClick={() => onAction(type)}
      className={`btn ${cls} flex-1 min-w-[120px] py-2.5`}>
      <Icon size={16} /> {label}
    </button>
  );

  return (
    <div className="space-y-5">
      <Link to="/m/leads" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
        <ArrowLeft size={16} /> Back to Leads
      </Link>

      {/* header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="grid place-items-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white text-2xl font-extrabold shrink-0">
            {l.name?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-extrabold text-ink-900">{l.name}</h1>
              <Badge value={l.status} map={STATUS_COLORS} />
            </div>
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-sm text-ink-500">
              <span>{l.lead_code}</span>
              {l.phone && <span className="inline-flex items-center gap-1.5"><Phone size={14} /> {l.phone}</span>}
              {l.email && <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {l.email}</span>}
              {l.country && <span className="inline-flex items-center gap-1.5"><MapPin size={14} /> {l.country}</span>}
              <span>Source: {l.source_name || "—"}</span>
            </div>
          </div>
          <div className="shrink-0 w-40"><p className="text-xs text-ink-400 uppercase mb-1">AI Score</p><ScorePill value={l.score} /></div>
        </div>

        {/* funnel progress */}
        <div className="flex items-center gap-1 mt-5">
          {FUNNEL.map((s, i) => (
            <div key={s} className="flex-1">
              <div className={`h-1.5 rounded-full ${i <= rank ? "bg-brand-500" : "bg-ink-200"}`} />
              <p className={`text-[11px] mt-1 capitalize ${i <= rank ? "text-brand-600 font-semibold" : "text-ink-400"}`}>{s}</p>
            </div>
          ))}
        </div>
      </div>

      {/* action buttons */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-1">Engage</h3>
        <p className="text-xs text-ink-400 mb-4">Har action lead activity me log hota hai aur status apne aap aage badhta hai.</p>
        <div className="flex flex-wrap gap-2">
          <ActionBtn type="call" icon={Phone} label="Call" cls="bg-emerald-50 text-emerald-700 hover:bg-emerald-100" />
          <ActionBtn type="whatsapp" icon={MessageCircle} label="WhatsApp" cls="bg-green-50 text-green-700 hover:bg-green-100" />
          <ActionBtn type="email" icon={Mail} label="Email" cls="bg-blue-50 text-blue-700 hover:bg-blue-100" />
          <ActionBtn type="proposal" icon={FileText} label="Send Proposal" cls="bg-violet-50 text-violet-700 hover:bg-violet-100" />
        </div>
      </div>

      {/* timeline */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Clock size={18} className="text-brand-600" /> Activity Timeline</h3>
        <div className="space-y-1">
          {d.activities.length === 0 && <EmptyState title="No activity yet" hint="Use the Engage buttons above." />}
          {d.activities.map((a, i) => {
            const cfg = ACT_ICON[a.activity_type] || ACT_ICON.note;
            return (
              <div key={a.id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className={`grid place-items-center w-9 h-9 rounded-xl ${cfg.tint} shrink-0`}><cfg.icon size={16} /></div>
                  {i < d.activities.length - 1 && <div className="w-px flex-1 bg-ink-200 my-1" />}
                </div>
                <div className="pb-5 min-w-0">
                  <p className="text-sm font-semibold text-ink-800 capitalize">{a.activity_type}</p>
                  <p className="text-xs text-ink-500">{a.remarks}</p>
                  <p className="text-[11px] text-ink-400 mt-0.5">{a.user_name || "—"} · {dt(a.created_at)}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* message modal for whatsapp/email */}
      <Modal open={!!msgModal} onClose={() => setMsgModal(null)} title={msgModal ? `Send ${msgModal.type === "whatsapp" ? "WhatsApp" : "Email"}` : ""}
        footer={<>
          <button className="btn-ghost" onClick={() => setMsgModal(null)}>Cancel</button>
          <button className="btn-primary" disabled={busy} onClick={() => engage(msgModal.type, msg)}><Send size={15} /> Send</button>
        </>}>
        {msgModal && (
          <div>
            <p className="text-sm text-ink-500 mb-3">To: <b>{l.name}</b>{(msgModal.type === "whatsapp" ? l.phone : l.email) ? ` (${msgModal.type === "whatsapp" ? l.phone : l.email})` : ""}</p>
            <textarea className="input min-h-[110px]" placeholder="Type your message…" value={msg} onChange={(e) => setMsg(e.target.value)} />
            <p className="text-xs text-ink-400 mt-2">Twilio configured ho to live bhejega, warna activity me log hoga.</p>
          </div>
        )}
      </Modal>

      {proposal && (
        <ProposalBuilder initial={proposal} onClose={() => setProposal(null)}
          onSaved={() => { setProposal(null); load(); }} />
      )}
    </div>
  );
}
