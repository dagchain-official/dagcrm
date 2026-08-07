import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Mail, Phone, CreditCard, Briefcase, Building2, UserCog,
  Calendar, DollarSign, Wallet, FileText, BarChart3, Network, UserCheck, Activity,
} from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState, Badge } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

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
  const [e, setE] = useState(null);
  const [j, setJ] = useState(null);   // journey — reporting line, clients, timeline
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.get(`/employees/${id}/`).then((r) => setE(r.data)).catch(() => setErr(true));
    api.get(`/employees/${id}/journey/`).then((r) => setJ(r.data)).catch(() => setJ(null));
  }, [id]);

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
    </div>
  );
}
