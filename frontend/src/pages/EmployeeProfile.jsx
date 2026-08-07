import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Mail, Phone, CreditCard, Briefcase, Building2, UserCog,
  Calendar, DollarSign, Wallet, FileText, BarChart3, Network, UserCheck, Activity,
  CheckCircle2, Circle, ShieldCheck,
} from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState, Badge, Modal } from "../components/ui";
import DataForm from "../components/DataForm";
import { useToast } from "../context/ToastContext";
import { STATUS_COLORS } from "../config/resources";

const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

// the fields collected in each profile step (basic is done on the create form)
const STEP_META = {
  personal: {
    label: "Personal details", fields: [
      { key: "dob", label: "Date of birth", type: "date" },
      { key: "nationality", label: "Nationality" },
      { key: "address", label: "Address" },
      { key: "emergency_contact", label: "Emergency contact (name)" },
      { key: "emergency_phone", label: "Emergency phone" },
    ],
  },
  documents: {
    label: "Documents", fields: [
      { key: "photo", label: "Photo", type: "file", accept: "image/*" },
      { key: "document", label: "Document (PDF)", type: "file", accept: "application/pdf,.pdf" },
    ],
  },
  compliance: {
    label: "Verification (passport / visa)", fields: [
      { key: "passport_no", label: "Passport no." },
      { key: "passport_expiry", label: "Passport expiry", type: "date" },
      { key: "visa_expiry", label: "Visa expiry", type: "date" },
    ],
  },
};

// an expiry row that warns when the date is near/past
function Expiry({ label, d }) {
  if (!d) return <Row icon={Calendar} label={label} value="—" />;
  const days = Math.ceil((new Date(d) - new Date()) / 86400000);
  const tint = days < 0 ? "text-rose-600" : days <= 60 ? "text-amber-600" : "text-ink-800";
  const note = days < 0 ? " (expired)" : days <= 60 ? ` (in ${days}d)` : "";
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-ink-100 last:border-0">
      <Calendar size={16} className="text-ink-400 shrink-0" />
      <span className="text-sm text-ink-400 w-36 shrink-0">{label}</span>
      <span className={`text-sm font-medium ${tint}`}>{date(d)}{note}</span>
    </div>
  );
}

function Row({ icon: Icon, label, value, href }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-ink-100 last:border-0">
      <Icon size={16} className="text-ink-400 shrink-0" />
      <span className="text-sm text-ink-400 w-36 shrink-0">{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" className="text-sm font-medium text-brand-600 hover:underline truncate">{value}</a>
      ) : (
        <span className="text-sm font-medium text-ink-800 truncate">{value}</span>
      )}
    </div>
  );
}

export default function EmployeeProfile() {
  const { id } = useParams();
  const toast = useToast();
  const [e, setE] = useState(null);
  const [j, setJ] = useState(null);   // journey — reporting line, clients, timeline
  const [err, setErr] = useState(false);
  const [editStep, setEditStep] = useState(null);   // which step's edit modal is open
  const [saving, setSaving] = useState(false);

  const loadEmp = () => api.get(`/employees/${id}/`).then((r) => setE(r.data)).catch(() => setErr(true));
  useEffect(() => {
    loadEmp();
    api.get(`/employees/${id}/journey/`).then((r) => setJ(r.data)).catch(() => setJ(null));
  }, [id]);

  const saveStep = async (form) => {
    setSaving(true);
    const payload = { ...form };
    Object.keys(payload).forEach((k) => {
      const v = payload[k];
      if (v === "" || v == null || (typeof v === "string" && v.includes("/media/"))) delete payload[k];
    });
    const hasFile = Object.values(payload).some((v) => v instanceof File);
    let body = payload, cfg;
    if (hasFile) {
      const fd = new FormData();
      Object.entries(payload).forEach(([k, v]) => v != null && fd.append(k, v));
      body = fd; cfg = { headers: { "Content-Type": "multipart/form-data" } };
    }
    try {
      await api.patch(`/employees/${id}/`, body, cfg);
      toast.success("Profile updated");
      setEditStep(null);
      loadEmp();
    } catch { toast.error("Could not save"); } finally { setSaving(false); }
  };

  if (err) return <EmptyState title="Employee not found" />;
  if (!e) return <Spinner label="Loading profile…" />;

  return (
    <div className="space-y-5">
      <Link to="/hr/people" className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
        <ArrowLeft size={16} /> Back to People
      </Link>

      {/* header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {e.photo ? (
            <img src={e.photo} alt={e.user_name} className="w-20 h-20 rounded-2xl object-cover shrink-0" />
          ) : (
            <div className="grid place-items-center w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white text-3xl font-extrabold shrink-0">
              {(e.user_name || e.name || "?")[0]?.toUpperCase()}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-extrabold text-ink-900">{e.user_name || e.name}</h1>
              {e.status && <Badge value={e.status} map={STATUS_COLORS} />}
            </div>
            <p className="text-sm text-ink-500 mt-1">
              {[e.role_name, e.hierarchy_level_name, e.designation].filter(Boolean).join(" · ") || "—"}
            </p>
          </div>
          <Link to={`/employee-report`} className="chip !py-2 text-sm inline-flex items-center gap-1.5 shrink-0">
            <BarChart3 size={15} /> Full report
          </Link>
        </div>
      </div>

      {/* profile completion — step by step */}
      <div className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h3 className="font-bold text-ink-900 flex items-center gap-2"><ShieldCheck size={18} className="text-brand-600" /> Profile completion</h3>
          <span className="text-2xl font-extrabold text-brand-600 tabular-nums">{e.profile_completion}%</span>
        </div>
        <div className="h-3 rounded-full bg-ink-200 overflow-hidden mb-4">
          <div className="h-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all" style={{ width: `${e.profile_completion}%` }} />
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {(e.profile_steps || []).map((s, i) => {
            const editable = STEP_META[s.key];
            return (
              <div key={s.key} className={`rounded-xl border p-3 ${s.done ? "border-emerald-200 bg-emerald-500/5" : "border-ink-200 bg-ink-500/5"}`}>
                <div className="flex items-center gap-2">
                  {s.done ? <CheckCircle2 size={18} className="text-emerald-500" /> : <Circle size={18} className="text-ink-300" />}
                  <span className="text-xs font-bold text-ink-400 uppercase">Step {i + 1}</span>
                </div>
                <p className="text-sm font-semibold text-ink-800 mt-1">{s.label}</p>
                <p className="text-[11px] text-ink-400">{s.filled}/{s.total} done</p>
                {editable ? (
                  <button onClick={() => setEditStep(s.key)}
                    className={`text-xs mt-2 w-full justify-center ${s.done ? "chip !py-1.5" : "btn-primary !py-1.5 !px-3"}`}>
                    {s.done ? "Edit" : "Complete"}
                  </button>
                ) : (
                  <p className="text-[11px] text-ink-400 mt-2">{s.done ? "✓ done at creation" : "Set on the People form"}</p>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* details */}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Contact</h3>
          <Row icon={Mail} label="Email" value={e.email || "—"} />
          <Row icon={Phone} label="Phone" value={e.phone || "—"} />
          <Row icon={CreditCard} label="Employee ID" value={e.employee_id || "—"} />
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Role & Org</h3>
          <Row icon={Briefcase} label="Role" value={e.role_name || "—"} />
          <Row icon={Building2} label="Department" value={e.department_name || "—"} />
          <Row icon={UserCog} label="Reports to" value={e.manager_name || "—"} />
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Employment</h3>
          <Row icon={Calendar} label="Joining date" value={date(e.joining_date)} />
          <Row icon={DollarSign} label="Salary (monthly)" value={money(e.salary)} />
          <Row icon={Wallet} label="CTC (this month)" value={money(e.monthly_ctc)} />
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Personal</h3>
          <Row icon={Calendar} label="Date of birth" value={date(e.dob)} />
          <Row icon={Building2} label="Nationality" value={e.nationality || "—"} />
          <Row icon={Building2} label="Address" value={e.address || "—"} />
          <Row icon={Phone} label="Emergency" value={[e.emergency_contact, e.emergency_phone].filter(Boolean).join(" · ") || "—"} />
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Compliance</h3>
          <Row icon={CreditCard} label="Passport no." value={e.passport_no || "—"} />
          <Expiry label="Passport expiry" d={e.passport_expiry} />
          <Expiry label="Visa expiry" d={e.visa_expiry} />
        </div>
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Documents</h3>
          {e.photo && <Row icon={FileText} label="Photo" value="View photo" href={e.photo} />}
          {e.document
            ? <Row icon={FileText} label="Document" value="View / download" href={e.document} />
            : <p className="text-sm text-ink-400 py-2.5">No document uploaded.</p>}
        </div>
      </div>

      {/* ---- Journey / relationship 360 ---- */}
      {j && (
        <div className="grid lg:grid-cols-3 gap-5">
          {/* reporting line */}
          <div className="card p-5">
            <h3 className="font-bold text-ink-900 mb-3 flex items-center gap-2"><Network size={17} className="text-brand-600" /> Reporting line</h3>
            {(j.reporting?.managers || []).length > 0 && (
              <div className="mb-3">
                <p className="text-[11px] font-bold text-ink-400 uppercase mb-1.5">Reports up to</p>
                {j.reporting.managers.map((m) => (
                  <div key={m.id} className="flex items-center gap-2 p-2 rounded-lg bg-ink-500/5 mb-1">
                    <UserCog size={14} className="text-ink-400" />
                    <span className="text-sm text-ink-700"><b className="text-ink-900">{m.name}</b> · {m.role}</span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[11px] font-bold text-ink-400 uppercase mb-1.5">Direct reports ({(j.reporting?.reports || []).length})</p>
            {(j.reporting?.reports || []).length === 0 ? <p className="text-sm text-ink-400">None.</p> : (
              j.reporting.reports.map((r) => (
                <Link key={r.emp_id} to={`/hr/employee/${r.emp_id}`} className="flex items-center gap-2 p-2 rounded-lg bg-brand-500/10 mb-1 hover:bg-brand-500/20">
                  <UserCheck size={14} className="text-brand-600" />
                  <span className="text-sm text-ink-700"><b className="text-ink-900">{r.name}</b> · {r.role}</span>
                </Link>
              ))
            )}
          </div>

          {/* clients */}
          <div className="card p-5">
            <h3 className="font-bold text-ink-900 mb-3 flex items-center gap-2"><Briefcase size={17} className="text-brand-600" /> Clients ({(j.clients || []).length})</h3>
            {(j.clients || []).length === 0 ? <p className="text-sm text-ink-400">No clients assigned.</p> : (
              <div className="space-y-1.5 max-h-72 overflow-y-auto">
                {j.clients.map((c) => (
                  <Link key={c.id} to={`/customers/${c.id}`} className="flex items-center justify-between gap-2 p-2 rounded-lg bg-ink-500/5 hover:bg-ink-500/10">
                    <span className="text-sm text-ink-700 truncate"><b className="text-ink-900">{c.name}</b> <span className="text-xs text-ink-400">· {c.platform}</span></span>
                    <span className="text-xs font-semibold text-emerald-600 shrink-0">{money(c.revenue)}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* timeline */}
          <div className="card p-5">
            <h3 className="font-bold text-ink-900 mb-3 flex items-center gap-2"><Activity size={17} className="text-brand-600" /> Timeline</h3>
            {(j.timeline || []).length === 0 ? <p className="text-sm text-ink-400">No events yet.</p> : (
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {j.timeline.map((ev, i) => (
                  <div key={i} className="flex gap-2.5">
                    <div className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 shrink-0" />
                    <div>
                      <p className="text-sm text-ink-700">{ev.title}</p>
                      <p className="text-[11px] text-ink-400">{date(ev.date)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* step editor */}
      <Modal open={!!editStep} onClose={() => setEditStep(null)} title={editStep ? STEP_META[editStep]?.label : ""}>
        {editStep && (
          <DataForm
            fields={STEP_META[editStep].fields}
            initial={Object.fromEntries(STEP_META[editStep].fields.map((f) => [f.key, e[f.key] ?? ""]))}
            submitting={saving} onSubmit={saveStep} onCancel={() => setEditStep(null)} />
        )}
      </Modal>
    </div>
  );
}
