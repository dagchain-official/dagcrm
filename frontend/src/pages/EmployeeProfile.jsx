import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Mail, Phone, IdCard, Briefcase, Building2, UserCog,
  Calendar, DollarSign, Wallet, FileText, BarChart3,
} from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState, Badge } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

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
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.get(`/employees/${id}/`).then((r) => setE(r.data)).catch(() => setErr(true));
  }, [id]);

  if (err) return <EmptyState title="Employee not found" />;
  if (!e) return <Spinner label="Loading profile…" />;

  return (
    <div className="space-y-5 max-w-4xl">
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
      <div className="grid md:grid-cols-2 gap-5">
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-2">Contact</h3>
          <Row icon={Mail} label="Email" value={e.email || "—"} />
          <Row icon={Phone} label="Phone" value={e.phone || "—"} />
          <Row icon={IdCard} label="Employee ID" value={e.employee_id || "—"} />
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
          <h3 className="font-bold text-ink-900 mb-2">Documents</h3>
          {e.photo && <Row icon={FileText} label="Photo" value="View photo" href={e.photo} />}
          {e.document
            ? <Row icon={FileText} label="Document" value="View / download" href={e.document} />
            : <p className="text-sm text-ink-400 py-2.5">No document uploaded.</p>}
        </div>
      </div>
    </div>
  );
}
