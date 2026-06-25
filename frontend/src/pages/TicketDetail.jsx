import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, MessageSquare, Paperclip, FileText, Download, Upload,
  Clock, Send, User, Calendar,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Badge, Spinner, EmptyState } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";
import { useToast } from "../context/ToastContext";

const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const shortDt = (v) => (v ? new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");

// SLA resolution targets (hours) by priority
const SLA_TARGETS = { urgent: 4, high: 24, medium: 48, low: 72 };

const fmtDuration = (hrs) => {
  const total = Math.max(0, Math.round(hrs * 60));
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${h}h ${m}m`;
};

function Stat({ label, value, valueClass }) {
  return (
    <div>
      <p className="text-xs text-ink-400 uppercase tracking-wide">{label}</p>
      <p className={`text-xl font-extrabold mt-0.5 tabular-nums ${valueClass || "text-ink-900"}`}>{value}</p>
    </div>
  );
}

function Section({ children }) {
  return <div className="card p-5">{children}</div>;
}

export default function TicketDetail() {
  const { id } = useParams();
  const toast = useToast();
  const [t, setT] = useState(null);
  const [err, setErr] = useState(false);
  const [atts, setAtts] = useState([]);
  const [comment, setComment] = useState("");
  const [posting, setPosting] = useState(false);

  const loadTicket = () => api.get(`/tickets/${id}/`).then((r) => setT(r.data)).catch(() => { if (!t) setErr(true); });
  const loadAtts = () =>
    api.get(`/attachments/?ticket=${id}`)
      .then((r) => setAtts(Array.isArray(r.data) ? r.data : (r.data?.results || [])))
      .catch(() => {});

  usePolling(() => { loadTicket(); loadAtts(); }, 2000, [id]);   // live refresh

  const addComment = async () => {
    const text = comment.trim();
    if (!text) return;
    setPosting(true);
    try {
      await api.post("/ticket-comments/", { ticket: Number(id), comment: text });
      setComment("");
      loadTicket();
      toast.success("Comment added");
    } catch (e) {
      toast.error("Failed to add comment: " + (e.response?.data?.detail || e.message));
    } finally {
      setPosting(false);
    }
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("ticket", id);
    await api.post("/attachments/", fd, { headers: { "Content-Type": "multipart/form-data" } });
    e.target.value = "";
    loadAtts();
  };

  if (err) return <EmptyState title="Ticket not found" hint="It may have been deleted." />;
  if (!t) return <Spinner label="Loading ticket…" />;

  // SLA computation
  const targetHrs = SLA_TARGETS[t.priority] ?? 48;
  const elapsedHrs = t.created_at ? (Date.now() - new Date(t.created_at).getTime()) / 36e5 : 0;
  const remainingHrs = targetHrs - elapsedHrs;
  const isDone = t.status === "resolved" || t.status === "closed";
  const breached = !isDone && elapsedHrs > targetHrs;
  const pct = Math.min(100, Math.round((elapsedHrs / targetHrs) * 100));

  const barColor = isDone ? "bg-emerald-500" : breached ? "bg-rose-500" : pct >= 80 ? "bg-amber-500" : "bg-amber-400";
  const pill = isDone
    ? { cls: "bg-emerald-50 text-emerald-700", text: t.status === "closed" ? "Closed" : "Met" }
    : breached
      ? { cls: "bg-rose-50 text-rose-700", text: "Breached" }
      : { cls: "bg-amber-50 text-amber-700", text: `On track (${fmtDuration(remainingHrs)} left)` };

  const comments = t.comments || [];

  return (
    <div className="space-y-5">
      <Link to="/m/tickets" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
        <ArrowLeft size={16} /> Back to Tickets
      </Link>

      {/* header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-extrabold text-ink-900">{t.ticket_no}</h1>
            <p className="text-sm text-ink-500 mt-1">{t.customer_name}{t.category ? ` · ${t.category}` : ""}</p>
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-sm text-ink-500">
              <span className="inline-flex items-center gap-1.5"><User size={14} /> Agent: {t.assigned_name || "—"}</span>
              <span className="inline-flex items-center gap-1.5"><Calendar size={14} /> Opened: {date(t.created_at)}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge value={t.priority} map={STATUS_COLORS} />
            <Badge value={t.status} map={STATUS_COLORS} />
          </div>
        </div>
      </div>

      {/* SLA */}
      <Section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-ink-900 flex items-center gap-2"><Clock size={18} className="text-brand-600" /> SLA</h3>
          <span className={`badge ${pill.cls}`}>{pill.text}</span>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <Stat label="Elapsed" value={fmtDuration(elapsedHrs)} valueClass={breached ? "text-rose-600" : "text-ink-900"} />
          <Stat label="SLA Target" value={`${targetHrs}h`} />
          <Stat label="Priority" value={String(t.priority ?? "—")} valueClass="capitalize text-ink-900" />
        </div>
        <div className="w-full h-2 rounded-full bg-ink-200 overflow-hidden">
          <div className={`h-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
        </div>
      </Section>

      {/* comments */}
      <Section>
        <h3 className="font-bold text-ink-900 flex items-center gap-2 mb-4">
          <MessageSquare size={18} className="text-brand-600" /> Comments ({comments.length})
        </h3>
        <div className="space-y-2">
          {comments.map((c) => (
            <div key={c.id} className="flex items-start gap-3 p-3 rounded-2xl bg-ink-50">
              <div className="grid place-items-center w-9 h-9 rounded-xl bg-brand-100 text-brand-600 text-sm font-bold shrink-0">
                {c.user_name?.[0]?.toUpperCase() || "?"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-ink-800">{c.user_name || "—"}</p>
                <p className="text-sm text-ink-600 whitespace-pre-wrap break-words">{c.comment}</p>
              </div>
              <span className="text-[11px] text-ink-400 shrink-0">{shortDt(c.created_at)}</span>
            </div>
          ))}
          {comments.length === 0 && <EmptyState title="No comments yet" hint="Be the first to add one." />}
        </div>
        <div className="mt-4 space-y-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            placeholder="Write a comment…"
            className="input w-full resize-y"
          />
          <div className="flex justify-end">
            <button className="btn-primary text-sm" onClick={addComment} disabled={posting || !comment.trim()}>
              <Send size={15} /> Add Comment
            </button>
          </div>
        </div>
      </Section>

      {/* attachments */}
      <Section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-ink-900 flex items-center gap-2"><Paperclip size={18} className="text-brand-600" /> Attachments ({atts.length})</h3>
          <label className="btn-primary cursor-pointer text-sm">
            <Upload size={15} /> Upload
            <input type="file" className="hidden" onChange={upload} />
          </label>
        </div>
        <div className="space-y-2">
          {atts.map((a) => (
            <div key={a.id} className="flex items-center gap-3 p-3 rounded-2xl bg-ink-50">
              <div className="grid place-items-center w-9 h-9 rounded-xl bg-brand-100 text-brand-600 shrink-0"><FileText size={16} /></div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-ink-800 truncate">{a.name}</p>
                <p className="text-[11px] text-ink-400">{a.uploaded_by_name || "—"} · {shortDt(a.created_at)}</p>
              </div>
              <a href={a.file_url} target="_blank" rel="noreferrer" className="btn-ghost p-2 text-brand-600"><Download size={16} /></a>
            </div>
          ))}
          {atts.length === 0 && <EmptyState title="No attachments" hint="Upload files for this ticket." />}
        </div>
      </Section>
    </div>
  );
}
