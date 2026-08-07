import { useEffect, useState } from "react";
import { FileText, Send, Check, X, Clock, Inbox } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";
import { useToast } from "../context/ToastContext";

const TYPES = [
  ["visa", "Visa / Immigration"], ["letter", "Letter / Certificate"],
  ["reimbursement", "Reimbursement"], ["document", "Document"],
  ["leave", "Leave"], ["other", "Other"],
];
const STAGE = { manager: "Manager", hr: "HR", head: "Business Head" };
const STATUS_TINT = {
  pending: "bg-amber-50 text-amber-700", approved: "bg-emerald-50 text-emerald-700",
  rejected: "bg-rose-50 text-rose-600", cancelled: "bg-ink-100 text-ink-500",
};
const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const dt = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "");

function Chain({ r }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
      {(r.chain || []).map((s, i) => {
        const done = i < r.stage_index || r.status === "approved";
        const active = r.status === "pending" && i === r.stage_index;
        return (
          <span key={i} className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
            done ? "bg-emerald-50 text-emerald-700" : active ? "bg-amber-100 text-amber-700" : "bg-ink-100 text-ink-400"}`}>
            {STAGE[s] || s}{done ? " ✓" : active ? " • now" : ""}
          </span>
        );
      })}
    </div>
  );
}

function RequestCard({ r, onDecide, onAssign, people }) {
  const type = TYPES.find(([v]) => v === r.request_type)?.[1] || r.request_type;
  const [owner, setOwner] = useState(r.owner || "");
  const [due, setDue] = useState(r.due_date || "");
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-bold text-ink-900">{r.title}</p>
          <p className="text-xs text-ink-400">{type}{r.amount > 0 ? ` · ${money(r.amount)}` : ""}{r.start_date ? ` · ${dt(r.start_date)}–${dt(r.end_date)}` : ""}
            {!r.is_mine && r.employee_name ? ` · ${r.employee_name}` : ""}</p>
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${STATUS_TINT[r.status]}`}>{r.status}</span>
      </div>
      {r.details && <p className="text-sm text-ink-500 mt-1.5">{r.details}</p>}
      {(r.owner_name || r.due_date) && (
        <p className="text-[11px] text-brand-600 mt-1.5 font-semibold">
          {r.owner_name ? `Owner: ${r.owner_name}` : ""}{r.owner_name && r.due_date ? " · " : ""}{r.due_date ? `Due ${dt(r.due_date)}` : ""}
        </p>
      )}
      <Chain r={r} />
      {onAssign && r.can_approve && (
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-ink-100">
          <span className="text-[11px] font-semibold text-ink-400">Assign HR task:</span>
          <select className="input !py-1 !text-xs !w-auto" value={owner} onChange={(e) => setOwner(e.target.value)}>
            <option value="">Owner…</option>
            {(people || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input type="date" className="input !py-1 !text-xs !w-auto" value={due} onChange={(e) => setDue(e.target.value)} />
          <button onClick={() => onAssign(r.id, owner, due)} className="btn text-xs px-2.5 py-1 bg-brand-50 text-brand-700 hover:bg-brand-100">Assign</button>
        </div>
      )}
      {onDecide && r.can_approve && (
        <div className="flex gap-2 mt-3">
          <button onClick={() => onDecide(r.id, "approve")} className="btn text-xs px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"><Check size={14} /> Approve</button>
          <button onClick={() => onDecide(r.id, "reject")} className="btn text-xs px-3 py-1.5 bg-rose-50 text-rose-600 hover:bg-rose-100"><X size={14} /> Reject</button>
        </div>
      )}
      {r.approvals?.length > 0 && (
        <div className="mt-3 pt-2 border-t border-ink-100 space-y-1">
          {r.approvals.map((a) => (
            <p key={a.id} className="text-[11px] text-ink-400">
              <b className={a.decision === "reject" ? "text-rose-600" : "text-emerald-600"}>{a.decision}d</b> by {a.approver_name || "—"} ({STAGE[a.stage] || a.stage}){a.comment ? ` · ${a.comment}` : ""}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function HrRequests() {
  const toast = useToast();
  const [rows, setRows] = useState(null);
  const [people, setPeople] = useState([]);
  const [form, setForm] = useState({ request_type: "reimbursement", title: "", details: "", amount: "", start_date: "", end_date: "" });
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/hr-requests/").then((r) => setRows(r.data.results || r.data || [])).catch(() => setRows([]));
  useEffect(() => {
    load();
    api.get("/users/assignable/").then(({ data }) => setPeople(data.results || data || [])).catch(() => {});
  }, []);

  const assign = async (id, owner, due_date) => {
    try {
      await api.post(`/hr-requests/${id}/assign/`, { owner: owner || null, due_date: due_date || null });
      toast.success("Assigned");
      load();
    } catch (err) { toast.error(err.response?.data?.detail || "Could not assign"); }
  };

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const submit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error("Add a title"); return; }
    setBusy(true);
    try {
      const body = { ...form };
      if (body.amount === "") delete body.amount;
      Object.keys(body).forEach((k) => body[k] === "" && delete body[k]);
      await api.post("/hr-requests/", body);
      toast.success("Request submitted");
      setForm({ request_type: "reimbursement", title: "", details: "", amount: "", start_date: "", end_date: "" });
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not submit");
    } finally { setBusy(false); }
  };

  const decide = async (id, decision) => {
    try {
      await api.post(`/hr-requests/${id}/${decision}/`);
      toast.success(decision === "approve" ? "Approved" : "Rejected");
      load();
    } catch (err) { toast.error(err.response?.data?.detail || "Failed"); }
  };

  if (!rows) return <Spinner label="Loading requests…" />;
  const mine = rows.filter((r) => r.is_mine);
  const inbox = rows.filter((r) => r.can_approve);
  const needsDates = ["leave", "visa"].includes(form.request_type);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><FileText className="text-brand-600" /> Requests</h1>
        <p className="text-sm text-ink-400">Raise a visa / letter / reimbursement request — it routes through manager → HR → approval.</p>
      </div>

      {/* submit */}
      <form onSubmit={submit} className="card p-5 grid sm:grid-cols-2 gap-3">
        <div>
          <label className="label">Type</label>
          <select className="input" value={form.request_type} onChange={(e) => set("request_type", e.target.value)}>
            {TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Title</label>
          <input className="input" value={form.title} onChange={(e) => set("title", e.target.value)} placeholder="e.g. Salary certificate" />
        </div>
        {form.request_type === "reimbursement" && (
          <div>
            <label className="label">Amount ($)</label>
            <input className="input" type="number" step="0.01" value={form.amount} onChange={(e) => set("amount", e.target.value)} />
          </div>
        )}
        {needsDates && (
          <>
            <div><label className="label">From</label><input className="input" type="date" value={form.start_date} onChange={(e) => set("start_date", e.target.value)} /></div>
            <div><label className="label">To</label><input className="input" type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} /></div>
          </>
        )}
        <div className="sm:col-span-2">
          <label className="label">Details</label>
          <textarea className="input min-h-[70px]" value={form.details} onChange={(e) => set("details", e.target.value)} placeholder="Describe your request…" />
        </div>
        <div className="sm:col-span-2 flex justify-end">
          <button className="btn-primary" disabled={busy}><Send size={15} /> {busy ? "Submitting…" : "Submit request"}</button>
        </div>
      </form>

      {/* pending my approval */}
      {inbox.length > 0 && (
        <div>
          <h3 className="font-bold text-ink-900 mb-2 flex items-center gap-2"><Inbox size={17} className="text-amber-500" /> Pending my approval ({inbox.length})</h3>
          <div className="grid lg:grid-cols-2 gap-3">
            {inbox.map((r) => <RequestCard key={r.id} r={r} onDecide={decide} onAssign={assign} people={people} />)}
          </div>
        </div>
      )}

      {/* my requests */}
      <div>
        <h3 className="font-bold text-ink-900 mb-2 flex items-center gap-2"><Clock size={17} className="text-brand-600" /> My requests</h3>
        {mine.length === 0 ? <EmptyState title="No requests yet" hint="Submit one above." /> : (
          <div className="grid lg:grid-cols-2 gap-3">{mine.map((r) => <RequestCard key={r.id} r={r} />)}</div>
        )}
      </div>
    </div>
  );
}
