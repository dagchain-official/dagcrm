import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { GraduationCap, ArrowLeft, Users, ClipboardCheck } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState, Badge } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const dt = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");
const pct = (v) => (v == null || v === "" ? "—" : `${(Number(v) * 100).toFixed(0)}%`);

export default function TrainingModuleDetail() {
  const { id } = useParams();
  const [mod, setMod] = useState(null);
  const [assigns, setAssigns] = useState([]);
  const [assess, setAssess] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/training-modules/${id}/`).then((r) => setMod(r.data))
      .catch(() => setErr("Module not found."));
    api.get("/training-assignments/", { params: { module: id, page_size: 500 } })
      .then((r) => setAssigns(r.data.results || r.data || [])).catch(() => setAssigns([]));
    api.get("/assessments/", { params: { module: id, page_size: 500 } })
      .then((r) => setAssess(r.data.results || r.data || [])).catch(() => setAssess([]));
  }, [id]);

  if (err) return <EmptyState title="Not found" hint={err} />;
  if (!mod) return <Spinner label="Loading module…" />;

  const done = assigns.filter((a) => a.status === "completed").length;
  const counted = assigns.filter((a) => a.status !== "exempted").length;
  const compliance = counted ? `${((done / counted) * 100).toFixed(0)}%` : "—";

  return (
    <div className="space-y-5">
      <Link to="/hr/training" className="text-xs text-brand-600 inline-flex items-center gap-1 hover:underline">
        <ArrowLeft size={12} /> All modules
      </Link>

      {/* module header */}
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
              <GraduationCap className="text-brand-600" /> {mod.title}
            </h1>
            <p className="text-sm text-ink-400 mt-0.5">{mod.module_id} · {mod.category || "—"} · v{mod.version}</p>
          </div>
          <div className="flex gap-2">
            <span className={`badge ${mod.active ? "bg-emerald-50 text-emerald-700" : "bg-ink-100 text-ink-500"}`}>{mod.active ? "Active" : "Inactive"}</span>
            {mod.mandatory && <span className="badge bg-amber-50 text-amber-700">Mandatory</span>}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-3 gap-x-4 text-sm mt-4">
          {[
            ["Audience", mod.audience || "—"], ["Owner", mod.owner_name || "—"],
            ["Delivery", mod.delivery_mode || "—"], ["Duration", `${mod.duration_hours} h`],
            ["Frequency", mod.frequency || "—"], ["Pass mark", pct(mod.pass_mark)],
            ["Assigned", `${assigns.length}`], ["Compliance", compliance],
          ].map(([k, v]) => (
            <div key={k}><p className="text-[11px] text-ink-400 uppercase tracking-wide">{k}</p><p className="font-semibold text-ink-800">{v}</p></div>
          ))}
        </div>
        {mod.content_summary && <p className="text-sm text-ink-500 mt-4"><b className="text-ink-700">Content:</b> {mod.content_summary}</p>}
        {mod.learning_outcome && <p className="text-sm text-ink-500 mt-1"><b className="text-ink-700">Outcome:</b> {mod.learning_outcome}</p>}
      </div>

      {/* assignments for this module */}
      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><Users size={18} className="text-brand-600" /> Assignments <span className="text-sm font-normal text-ink-400">({assigns.length})</span></h3>
        {assigns.length === 0 ? (
          <EmptyState title="No assignments yet" hint="Assign this module to employees from the Assignments tab." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">Employee</th>
                  <th className="py-2.5 px-4">Assigned</th>
                  <th className="py-2.5 px-4">Due</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Score</th>
                  <th className="py-2.5 px-4">Compliance</th>
                </tr>
              </thead>
              <tbody>
                {assigns.map((a) => (
                  <tr key={a.id} className="border-t border-ink-100 hover:bg-ink-50/60">
                    <td className="py-2.5 px-4 font-medium text-ink-800">{a.employee_name}</td>
                    <td className="py-2.5 px-4 text-ink-500">{dt(a.assigned_date)}</td>
                    <td className="py-2.5 px-4 text-ink-500">{dt(a.due_date)}</td>
                    <td className="py-2.5 px-4"><Badge value={a.status} map={STATUS_COLORS} /></td>
                    <td className="py-2.5 px-4 text-right tabular-nums">{pct(a.latest_score)}</td>
                    <td className="py-2.5 px-4"><Badge value={a.compliance_flag} map={STATUS_COLORS} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* assessments for this module */}
      {assess.length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-ink-900 mb-4 flex items-center gap-2"><ClipboardCheck size={18} className="text-sky-600" /> Assessments <span className="text-sm font-normal text-ink-400">({assess.length})</span></h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                  <th className="py-2.5 px-4">Employee</th>
                  <th className="py-2.5 px-4">Date</th>
                  <th className="py-2.5 px-4 text-right">Attempt</th>
                  <th className="py-2.5 px-4 text-right">Score</th>
                  <th className="py-2.5 px-4">Result</th>
                  <th className="py-2.5 px-4">Certificate</th>
                </tr>
              </thead>
              <tbody>
                {assess.map((a) => (
                  <tr key={a.id} className="border-t border-ink-100 hover:bg-ink-50/60">
                    <td className="py-2.5 px-4 font-medium text-ink-800">{a.employee_name}</td>
                    <td className="py-2.5 px-4 text-ink-500">{dt(a.assessment_date)}</td>
                    <td className="py-2.5 px-4 text-right tabular-nums">{a.attempt_no}</td>
                    <td className="py-2.5 px-4 text-right tabular-nums">{pct(a.score)}</td>
                    <td className="py-2.5 px-4"><Badge value={a.result} map={STATUS_COLORS} /></td>
                    <td className="py-2.5 px-4 text-ink-500 font-mono text-xs">{a.certificate_id || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
