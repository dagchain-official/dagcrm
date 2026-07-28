import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Phone, MessageCircle, Mail, FileText, Mic, StickyNote,
  Calendar, MapPin, Target as TargetIcon, Clock, Send, Lock,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState, Modal, ScorePill } from "../components/ui";
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
const FUNNEL = ["new", "assigned", "attempted", "contacted", "qualified",
  "meeting_booked", "meeting_done", "negotiation", "converted"];

export default function LeadDetail() {
  const { id } = useParams();
  const toast = useToast();
  const [d, setD] = useState(null);
  const [err, setErr] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msgModal, setMsgModal] = useState(null); // {type}
  const [callModal, setCallModal] = useState(false);
  const [meetModal, setMeetModal] = useState(false);
  const [msg, setMsg] = useState("");
  const [subject, setSubject] = useState("");
  const [emailAccounts, setEmailAccounts] = useState([]);
  const [emailFrom, setEmailFrom] = useState("");
  const [history, setHistory] = useState([]);   // past messages/emails in the thread
  const [histLoading, setHistLoading] = useState(false);

  const load = () => api.get(`/leads/${id}/overview/`).then((r) => setD(r.data)).catch(() => { if (!d) setErr(true); });
  usePolling(load, 2000, [id]);   // live refresh; re-fetches immediately when id changes

  // when the email modal opens, load the user's configured from-accounts
  useEffect(() => {
    if (msgModal?.type !== "email") return;
    api.get("/email-accounts/").then((r) => {
      const active = (r.data || []).filter((a) => a.is_active);
      setEmailAccounts(active);
      const def = active.find((a) => a.is_default) || active[0];
      setEmailFrom(def ? String(def.id) : "");
    }).catch(() => setEmailAccounts([]));
  }, [msgModal]);

  // load the past conversation (WhatsApp / Email) for the thread view.
  // oldest first so it reads top -> bottom like a chat.
  const loadHistory = () => {
    if (!msgModal) return;
    setHistLoading(true);
    api.get("/communications/", { params: { lead: id, channel: msgModal.type, page_size: 100 } })
      .then((r) => {
        const rows = r.data.results || r.data || [];
        setHistory([...rows].sort((a, b) => new Date(a.created_at) - new Date(b.created_at)));
      })
      .catch(() => setHistory([]))
      .finally(() => setHistLoading(false));
  };
  useEffect(() => {
    if (!msgModal) { setHistory([]); return; }
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [msgModal, id]);

  const engage = async (type, opts = {}) => {
    setBusy(true);
    try {
      const prev = d.lead.status;
      const { data } = await api.post(`/leads/${id}/engage/`, {
        type,
        place_call: opts.place_call || false,
        message: opts.message || "",
        subject: opts.subject || "",
        email_account: opts.emailAccount || null,
        remarks: opts.remarks || "",
        duration_min: opts.duration_min || 0,
        outcome: opts.outcome || "",
        meeting_status: opts.meeting_status || "",
        meeting_at: opts.meeting_at || null,
      });
      await load();
      const t = data.telephony;
      // Report what actually happened on the line, not just "logged".
      if (opts.place_call) {
        if (t?.live) toast.success("Calling now — your phone will ring, then it dials the lead");
        else if (t?.error) toast.error(`Call failed: ${t.error}`);
        else toast.info(t?.note || "Logged — live calling isn't set up");
      } else {
        const liveNote = t?.note ? ` — ${t.note}` : t?.live ? " (live)" : "";
        toast.success(`${type === "call" ? "Logged" : type === "whatsapp" ? "WhatsApp sent" : type === "email" ? "Email sent" : "Logged"}${liveNote}`);
      }
      if (data.lead.status !== prev) toast.info(`Status auto-advanced: ${prev} → ${data.lead.status}`);
      if (type === "whatsapp" || type === "email") {
        // keep the chat modal open so the conversation can continue — clear the
        // box and refresh the thread so the just-sent message appears.
        setMsg("");
        loadHistory();
      } else {
        setMsgModal(null);
      }
    } catch (e) {
      toast.error("Action failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setBusy(false);
    }
  };

  if (err) return <EmptyState title="Lead not found" />;
  if (!d) return <Spinner label="Loading lead…" />;
  const l = d.lead;
  if (l.locked) {
    return (
      <div className="space-y-5">
        <Link to="/m/leads" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
          <ArrowLeft size={16} /> Back to Leads
        </Link>
        <div className="card p-10 text-center max-w-lg mx-auto">
          <div className="grid place-items-center w-14 h-14 rounded-2xl bg-amber-100 text-amber-600 mx-auto mb-4">
            <Lock size={24} />
          </div>
          <h2 className="text-xl font-extrabold text-ink-900">This lead is locked</h2>
          <p className="text-sm text-ink-500 mt-2">
            Work your earlier lead first — log a call, message or any activity on it, and this one unlocks automatically.
          </p>
          <Link to="/m/leads" className="btn-primary inline-flex mt-5">Go to my leads</Link>
        </div>
      </div>
    );
  }
  const rank = FUNNEL.indexOf(l.status);

  const onAction = (type) => {
    if (type === "whatsapp" || type === "email") return setMsgModal({ type });
    if (type === "call") return setCallModal(true);
    if (type === "meeting") return setMeetModal(true);
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

        {/* Lead Register qualifiers + SLA analytics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-ink-100 text-sm">
          {[
            ["Priority", <Badge value={l.priority} map={STATUS_COLORS} />],
            ["Expected value", `$${Number(l.expected_value || 0).toLocaleString()}`],
            ["Probability", `${l.probability || 0}%`],
            ["Weighted pipeline", `$${Number(l.weighted_pipeline || 0).toLocaleString()}`],
            ["First response", l.first_response_min == null ? "—" : `${l.first_response_min} min`],
            ["SLA", <Badge value={l.sla_status} map={STATUS_COLORS} />],
            ["Days open", l.days_open],
            ["Follow-up", <Badge value={l.follow_up_status} map={STATUS_COLORS} />],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[11px] text-ink-400 uppercase tracking-wide">{k}</p>
              <p className="font-semibold text-ink-800 mt-0.5">{v}</p>
            </div>
          ))}
        </div>
        {l.status === "lost" && l.lost_reason && (
          <p className="text-sm text-rose-600 mt-3"><b>Lost reason:</b> {l.lost_reason}</p>
        )}
      </div>

      {/* action buttons */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-1">Engage</h3>
        <p className="text-xs text-ink-400 mb-4">Every action is logged in the lead activity and the status advances automatically.</p>
        <div className="flex flex-wrap gap-2">
          <ActionBtn type="call" icon={Phone} label="Log Call" cls="bg-emerald-50 text-emerald-700 hover:bg-emerald-100" />
          <ActionBtn type="whatsapp" icon={MessageCircle} label="WhatsApp" cls="bg-green-50 text-green-700 hover:bg-green-100" />
          <ActionBtn type="email" icon={Mail} label="Email" cls="bg-blue-50 text-blue-700 hover:bg-blue-100" />
          <ActionBtn type="meeting" icon={Calendar} label="Meeting" cls="bg-amber-50 text-amber-700 hover:bg-amber-100" />
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
                  <p className="text-sm font-semibold text-ink-800 capitalize flex flex-wrap items-center gap-1.5">
                    {a.activity_type.replace(/_/g, " ")}
                    {a.outcome && <span className="badge bg-brand-50 text-brand-700">{a.outcome.replace(/_/g, " ")}</span>}
                    {a.meeting_status && <span className="badge bg-amber-50 text-amber-700">{a.meeting_status.replace(/_/g, " ")}</span>}
                    {Number(a.duration_min) > 0 && <span className="text-[11px] font-normal text-ink-400">· {a.duration_min} min</span>}
                  </p>
                  <p className="text-xs text-ink-500">{a.remarks}</p>
                  <p className="text-[11px] text-ink-400 mt-0.5">{a.user_name || "—"} · {dt(a.created_at)}{a.meeting_at ? ` · meeting ${dt(a.meeting_at)}` : ""}</p>
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
          <button className="btn-primary" disabled={busy}
            onClick={() => engage(msgModal.type, { message: msg, subject, emailAccount: emailFrom })}>
            <Send size={15} /> Send
          </button>
        </>}>
        {msgModal && (
          <div className="space-y-3">
            <p className="text-sm text-ink-500">To: <b>{l.name}</b>{(msgModal.type === "whatsapp" ? l.phone : l.email) ? ` (${msgModal.type === "whatsapp" ? l.phone : l.email})` : ""}</p>

            {msgModal.type === "email" && (
              <>
                <div>
                  <label className="label">From</label>
                  {emailAccounts.length > 0 ? (
                    <select className="input" value={emailFrom} onChange={(e) => setEmailFrom(e.target.value)}>
                      {emailAccounts.map((a) => (
                        <option key={a.id} value={a.id}>{a.label} — {a.from_email}{a.is_default ? " (default)" : ""}</option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
                      No business email configured. Add one in <Link to="/profile" className="underline font-medium">Settings</Link> to send from your own address — for now it'll just be logged.
                    </p>
                  )}
                </div>
                <div>
                  <label className="label">Subject</label>
                  <input className="input" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
                </div>
              </>
            )}

            {/* conversation history — past messages/emails with this lead */}
            <div>
              <label className="label">Conversation history</label>
              {histLoading ? (
                <p className="text-xs text-ink-400 py-3 text-center">Loading…</p>
              ) : history.length === 0 ? (
                <p className="text-xs text-ink-400 py-4 text-center bg-ink-50 rounded-xl">
                  No previous {msgModal.type === "whatsapp" ? "WhatsApp messages" : "emails"} with this lead yet.
                </p>
              ) : (
                <div className="max-h-56 overflow-y-auto space-y-2 p-3 rounded-xl bg-ink-50 border border-ink-100">
                  {history.map((c) => (
                    <div key={c.id} className={`flex ${c.direction === "outbound" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[78%] px-3 py-2 rounded-2xl text-sm ${c.direction === "outbound"
                        ? "bg-brand-600 text-white rounded-br-sm" : "bg-white border border-ink-200 text-ink-800 rounded-bl-sm"}`}>
                        <p className="whitespace-pre-line break-words">{c.message}</p>
                        <p className={`text-[10px] mt-0.5 ${c.direction === "outbound" ? "text-white/60" : "text-ink-400"}`}>
                          {c.direction === "inbound" ? "Received" : "Sent"} · {dt(c.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <textarea className="input min-h-[90px]" placeholder="Type your message…" value={msg} onChange={(e) => setMsg(e.target.value)} />
            {msgModal.type === "whatsapp"
              ? <p className="text-xs text-ink-400">If Twilio is configured this sends live, otherwise it's logged in the activity.</p>
              : <p className="text-xs text-ink-400">A real email is sent via the selected account's SMTP; otherwise it's logged in the activity.</p>}
          </div>
        )}
      </Modal>

      {callModal && (
        <CallModal lead={l} busy={busy} onClose={() => setCallModal(false)}
          onCall={() => engage("call", { place_call: true, remarks: "Call placed" })}
          onSubmit={(payload) => engage("call", payload).then(() => setCallModal(false))} />
      )}
      {meetModal && (
        <MeetingModal busy={busy} onClose={() => setMeetModal(false)}
          onSubmit={(payload) => engage("meeting", payload).then(() => setMeetModal(false))} />
      )}
    </div>
  );
}

const OUTCOMES = [
  ["connected", "Connected"], ["interested", "Interested"], ["callback", "Callback Requested"],
  ["meeting_booked", "Meeting Booked"], ["no_answer", "No Answer"], ["busy", "Busy"],
  ["voicemail", "Voicemail"], ["wrong_number", "Wrong Number"], ["not_interested", "Not Interested"],
  ["converted", "Converted"],
];
const MEETING_STATUSES = [
  ["scheduled", "Scheduled"], ["confirmed", "Confirmed"], ["completed", "Completed"],
  ["cancelled", "Cancelled"], ["no_show", "No Show"], ["rescheduled", "Rescheduled"],
];

// Log a call: outcome + duration + notes. The outcome auto-moves the lead's
// status. "Call now" places a Twilio call as a separate step.
function CallModal({ lead, busy, onClose, onSubmit, onCall }) {
  const [outcome, setOutcome] = useState("connected");
  const [duration, setDuration] = useState("");
  const [notes, setNotes] = useState("");
  return (
    <Modal open onClose={onClose} title={`Log call — ${lead.name}`}>
      <div className="space-y-3">
        {/* the number, visible so an agent can dial it directly from their phone */}
        <a href={lead.phone ? `tel:${lead.phone}` : undefined}
          className={`flex items-center justify-between gap-2 rounded-xl px-4 py-3 ${lead.phone ? "bg-brand-50 text-brand-700" : "bg-ink-50 text-ink-400"}`}>
          <span className="inline-flex items-center gap-2 text-sm font-semibold"><Phone size={15} /> {lead.phone || "No phone number on this lead"}</span>
          {lead.phone && <span className="text-xs font-medium">Tap to dial</span>}
        </a>
        <div>
          <label className="label">Outcome</label>
          <select className="input" value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            {OUTCOMES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Duration (minutes)</label>
          <input className="input" type="number" step="0.5" min="0" value={duration}
            onChange={(e) => setDuration(e.target.value)} placeholder="e.g. 5" />
        </div>
        <div>
          <label className="label">What was discussed?</label>
          <textarea className="input min-h-[90px]" value={notes} onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes about the call…" />
        </div>
        <p className="text-xs text-ink-400">The outcome auto-updates the lead's status (e.g. Interested → Qualified, Meeting Booked → Meeting Booked, Not Interested → Nurture).</p>
        <div className="flex justify-between gap-2 pt-1">
          <button className="chip !py-2 inline-flex items-center gap-1.5" disabled={busy || !lead.phone}
            onClick={onCall} title={lead.phone ? "Place a Twilio call" : "No phone number"}>
            <Phone size={14} /> Call now
          </button>
          <button className="btn-primary" disabled={busy}
            onClick={() => onSubmit({ outcome, duration_min: duration || 0, remarks: notes })}>
            {busy ? "Saving…" : "Save log"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// Log / schedule a meeting: status + date + notes. The status moves the lead
// (Scheduled/Confirmed → Meeting Booked, Completed → Meeting Done).
function MeetingModal({ busy, onClose, onSubmit }) {
  const [status, setStatus] = useState("scheduled");
  const [when, setWhen] = useState("");
  const [notes, setNotes] = useState("");
  return (
    <Modal open onClose={onClose} title="Log meeting">
      <div className="space-y-3">
        <div>
          <label className="label">Meeting status</label>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            {MEETING_STATUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Date &amp; time</label>
          <input className="input" type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
        </div>
        <div>
          <label className="label">Notes</label>
          <textarea className="input min-h-[80px]" value={notes} onChange={(e) => setNotes(e.target.value)}
            placeholder="Agenda / outcome…" />
        </div>
        <div className="flex justify-end pt-1">
          <button className="btn-primary" disabled={busy}
            onClick={() => onSubmit({ meeting_status: status, meeting_at: when || null, remarks: notes })}>
            {busy ? "Saving…" : "Save meeting"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
