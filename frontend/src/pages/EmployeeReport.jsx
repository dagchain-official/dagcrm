import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText, DollarSign, Trophy, Target, Clock, Calendar, MapPin,
  Phone, StickyNote, TrendingUp, UserCheck, FileSpreadsheet, FileDown,
} from "lucide-react";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const money = (v) => `$${Number(v || 0).toLocaleString()}`;
const mins = (m) => { const h = Math.floor((m || 0) / 60), x = (m || 0) % 60; return h ? `${h}h ${x}m` : `${x}m`; };

const cell = (c, r) => (c.fmt ? c.fmt(r[c.key], r) : (r[c.key] ?? ""));

// Fixed per-employee columns (All-employees view + exports). Dynamic KPI-metric
// columns (from the backend's metric_cols) are appended after these.
const FIXED_COLS = [
  { key: "employee", label: "Employee", left: true }, { key: "role", label: "Role", left: true },
  { key: "revenue", label: "Revenue", fmt: money }, { key: "overall", label: "Score" },
  { key: "rank", label: "Rank", fmt: (v) => `#${v}` }, { key: "suggestion", label: "Suggestion", left: true },
  { key: "target_pct", label: "Target %", fmt: (v) => `${v}%` },
  { key: "revenue_score", label: "Rev score" }, { key: "growth_score", label: "Growth score" },
  { key: "activity_score", label: "Activity score" }, { key: "conversion_pct", label: "Conv %", fmt: (v) => `${v}%` },
  { key: "leads_owned", label: "Leads" }, { key: "leads_open", label: "Open" },
  { key: "leads_converted", label: "Converted" }, { key: "leads_lost", label: "Lost" },
  { key: "converted_mo", label: "Conv (mo)" }, { key: "weighted_pipeline", label: "Wtd pipeline", fmt: money },
  { key: "calls", label: "Calls" }, { key: "notes", label: "Notes" }, { key: "tickets", label: "Tickets" },
  { key: "meetings", label: "Meetings" }, { key: "active_min", label: "Active", fmt: mins },
  { key: "idle_min", label: "Idle", fmt: mins }, { key: "present_days", label: "Present" },
  { key: "absent_days", label: "Absent" }, { key: "hours", label: "Hours", fmt: (v) => `${v}h` },
];

function exportCsv(name, cols, rows) {
  const lines = rows.map((r) => cols.map((c) => `"${String(cell(c, r)).replace(/"/g, '""')}"`).join(","));
  const csv = [cols.map((c) => c.label).join(","), ...lines].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
  const a = document.createElement("a"); a.href = url; a.download = `${name}.csv`; a.click();
  URL.revokeObjectURL(url);
}

function exportPdf(name, cols, rows) {
  const doc = new jsPDF({ orientation: "landscape" });
  doc.setFontSize(16); doc.setTextColor("#4f46e5"); doc.text(`DAGOS — ${name}`, 14, 16);
  doc.setFontSize(9); doc.setTextColor("#94a3b8"); doc.text(new Date().toLocaleString(), 14, 22);
  autoTable(doc, {
    startY: 26, head: [cols.map((c) => c.label)],
    body: rows.map((r) => cols.map((c) => String(cell(c, r)))),
    styles: { fontSize: 6, cellPadding: 1.5 }, headStyles: { fillColor: [79, 70, 229] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });
  doc.save(`${name}.pdf`);
}
const dt = (v) => (v ? new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—");
const day = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "—");

function Tile({ icon: Icon, label, value, sub, tint }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-ink-400 text-xs mb-1.5">
        <span className={`grid place-items-center w-7 h-7 rounded-lg ${tint}`}><Icon size={15} /></span>
        {label}
      </div>
      <p className="text-xl font-extrabold text-ink-900 tabular-nums leading-tight">{value}</p>
      {sub && <p className="text-[11px] text-ink-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <div className="card p-5">
      <h3 className="font-bold text-ink-900 mb-3 flex items-center gap-2">
        {Icon && <Icon size={17} className="text-brand-600" />} {title}
      </h3>
      {children}
    </div>
  );
}

export default function EmployeeReport() {
  const now = new Date();
  const [emps, setEmps] = useState([]);
  const [sel, setSel] = useState("all");   // default view: the all-employees table
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [rep, setRep] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/reports/employee-report/").then((r) => setEmps(r.data.employees || [])).catch(() => setEmps([]));
  }, []);

  useEffect(() => {
    if (!sel) { setRep(null); return; }
    setLoading(true);
    const params = sel === "all" ? { all: 1, month, year } : { employee: sel, month, year };
    api.get("/reports/employee-report/", { params })
      .then((r) => setRep(r.data)).catch(() => setRep(null)).finally(() => setLoading(false));
  }, [sel, month, year]);

  const p = rep?.performance;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <FileText className="text-brand-600" /> Employee Report
        </h1>
        <p className="text-sm text-ink-400">Pick an employee to see everything about them in one place.</p>
      </div>

      {/* controls */}
      <div className="card p-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[220px]">
          <label className="label">Employee</label>
          <select className="input" value={sel} onChange={(e) => setSel(e.target.value)}>
            <option value="">Select an employee…</option>
            <option value="all">All employees (table)</option>
            {emps.map((e) => <option key={e.id} value={e.id}>{e.name}{e.role ? ` — ${e.role}` : ""}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Month</label>
          <select className="input" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Year</label>
          <select className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[year + 1, year, year - 1, year - 2].filter((v, i, a) => a.indexOf(v) === i).map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {!sel && <EmptyState title="No employee selected" hint="Choose someone from the dropdown above." />}
      {sel && loading && <Spinner label="Building report…" />}
      {sel && sel !== "all" && !loading && rep?.found === false && <EmptyState title="No data" hint="This employee could not be loaded." />}

      {/* ALL employees — one row each, every metric, with Excel / PDF export */}
      {sel === "all" && !loading && rep?.rows && (() => {
        const cols = [...FIXED_COLS, ...(rep.metric_cols || []).map((n) => ({ key: n, label: n }))];
        const fname = `Employee Report ${MONTHS[month - 1]} ${year}`;
        return (
          <div className="card p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <h3 className="font-bold text-ink-900">All employees · {MONTHS[month - 1]} {year} ({rep.rows.length})</h3>
              <div className="flex gap-2">
                <button onClick={() => exportCsv(fname, cols, rep.rows)}
                  className="chip !py-2 text-sm inline-flex items-center gap-1.5"><FileSpreadsheet size={15} /> Excel</button>
                <button onClick={() => exportPdf(fname, cols, rep.rows)}
                  className="chip !py-2 text-sm inline-flex items-center gap-1.5"><FileDown size={15} /> PDF</button>
              </div>
            </div>
            {rep.rows.length === 0 ? <EmptyState title="No employees" hint="Nothing in your scope." /> : (
              <div className="overflow-x-auto">
                <table className="text-sm">
                  <thead>
                    <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                      {cols.map((c) => (
                        <th key={c.key} className={`py-2.5 px-3 font-semibold whitespace-nowrap ${c.left ? "" : "text-right"}`}>{c.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rep.rows.map((r, i) => (
                      <tr key={i} className="border-t border-ink-100 hover:bg-ink-50/60">
                        {cols.map((c) => (
                          <td key={c.key} className={`py-2.5 px-3 whitespace-nowrap ${c.left ? "font-medium text-ink-900" : "text-right tabular-nums text-ink-600"}`}>
                            {cell(c, r)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })()}

      {sel && sel !== "all" && !loading && rep?.found && (
        <>
          {/* profile */}
          <div className="card p-5 bg-gradient-to-br from-brand-600 to-brand-500 text-white border-0">
            <p className="text-2xl font-extrabold">{rep.profile.name}</p>
            <p className="text-sm text-white/80">
              {[rep.profile.role, rep.profile.level, rep.profile.manager ? `Reports to ${rep.profile.manager}` : null].filter(Boolean).join(" · ")}
            </p>
            <p className="text-xs text-white/60 mt-1">{MONTHS[rep.month - 1]} {rep.year} · {rep.profile.email}</p>
          </div>

          {/* headline tiles */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Tile icon={DollarSign} label="Revenue" value={money(rep.revenue)} tint="bg-emerald-100 text-emerald-600" />
            <Tile icon={Trophy} label="Performance" value={p ? `${p.overall}` : "—"} sub={p ? `Rank #${p.rank} · ${p.target_attainment}% of target` : ""} tint="bg-amber-100 text-amber-600" />
            <Tile icon={UserCheck} label="Conversion" value={`${rep.leads.conversion_rate}%`} sub={`${rep.leads.converted}/${rep.leads.owned} leads`} tint="bg-brand-100 text-brand-600" />
            <Tile icon={Clock} label="Attendance" value={`${rep.attendance.hours}h`} sub={`${rep.attendance.present} present · ${rep.attendance.absent} absent`} tint="bg-blue-100 text-blue-600" />
          </div>

          {/* performance breakdown */}
          {p && (
            <Section title="Performance scorecard" icon={Trophy}>
              {p.suggestion && (
                <div className="mb-4 flex items-center gap-2">
                  <span className="text-sm text-ink-500">AI recommendation:</span>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                    p.suggestion.startsWith("Promotion") ? "bg-emerald-50 text-emerald-700"
                      : p.suggestion === "On track" ? "bg-brand-50 text-brand-700"
                        : p.suggestion === "Needs improvement" ? "bg-amber-50 text-amber-700"
                          : "bg-rose-50 text-rose-600"}`}>
                    {p.suggestion}
                  </span>
                  {p.attendance_pct != null && <span className="text-xs text-ink-400">· attendance {p.attendance_pct}%</span>}
                </div>
              )}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Tile icon={DollarSign} label={`Revenue score (${p.weights.revenue}%)`} value={p.revenue_score} tint="bg-emerald-100 text-emerald-600" />
                <Tile icon={TrendingUp} label={`Growth score (${p.weights.growth}%)`} value={p.growth_score} tint="bg-violet-100 text-violet-600" />
                <Tile icon={Phone} label={`Activity score (${p.weights.activity}%)`} value={p.activity_score} tint="bg-blue-100 text-blue-600" />
                <Tile icon={Target} label="Target attainment" value={`${p.target_attainment}%`} tint="bg-amber-100 text-amber-600" />
              </div>
            </Section>
          )}

          {/* leads + activity */}
          <div className="grid lg:grid-cols-2 gap-5">
            <Section title="Leads" icon={UserCheck}>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[["Owned", rep.leads.owned], ["Open", rep.leads.open], ["Converted", rep.leads.converted],
                  ["Lost", rep.leads.lost], ["Converted (mo)", rep.leads.converted_month], ["Weighted pipeline", money(rep.leads.weighted_pipeline)]].map(([l, v]) => (
                  <div key={l} className="rounded-xl bg-ink-500/5 p-3">
                    <p className="text-lg font-extrabold text-ink-900 tabular-nums">{v}</p>
                    <p className="text-[11px] text-ink-400">{l}</p>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Activity (this month)" icon={Phone}>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[["Calls", rep.activity.calls], ["Notes", rep.activity.notes], ["Tickets", rep.activity.tickets],
                  ["Meetings", rep.meetings_month], ["Active", mins(rep.activity.active)], ["Idle", mins(rep.activity.idle)]].map(([l, v]) => (
                  <div key={l} className="rounded-xl bg-ink-500/5 p-3">
                    <p className="text-lg font-extrabold text-ink-900 tabular-nums">{v}</p>
                    <p className="text-[11px] text-ink-400">{l}</p>
                  </div>
                ))}
              </div>
            </Section>
          </div>

          {/* KPI metrics */}
          {rep.metrics.length > 0 && (
            <Section title="KPI metrics" icon={TrendingUp}>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {rep.metrics.map((m, i) => (
                  <div key={i} className="rounded-xl bg-ink-500/5 p-3">
                    <p className="text-lg font-extrabold text-ink-900 tabular-nums">{m.value}{m.unit ? ` ${m.unit}` : ""}</p>
                    <p className="text-[11px] text-ink-400">{m.metric}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* meetings + field visits */}
          <Section title="Meetings & field visits" icon={Calendar}>
            {rep.meetings.length === 0 ? <p className="text-sm text-ink-400">No meetings logged.</p> : (
              <div className="space-y-2">
                {rep.meetings.map((m, i) => (
                  <div key={i} className="flex flex-wrap items-center gap-x-3 gap-y-1 p-2.5 rounded-xl bg-ink-500/5">
                    <Link to={`/leads/${m.lead_id}`} className="text-sm font-semibold text-brand-600 hover:underline">{m.lead}</Link>
                    {m.status && <span className="badge bg-amber-50 text-amber-700">{m.status.replace(/_/g, " ")}</span>}
                    <span className="text-xs text-ink-400">{dt(m.at)}</span>
                    {m.planned && <span className="text-xs text-ink-500 flex items-center gap-1"><MapPin size={12} /> Planned: {m.planned}</span>}
                    {m.reached && <a href={m.map} target="_blank" rel="noreferrer" className="text-xs text-brand-600 hover:underline flex items-center gap-1"><MapPin size={12} /> Reached: {m.reached}</a>}
                  </div>
                ))}
              </div>
            )}
          </Section>

          {/* overdue follow-ups */}
          {rep.overdue_followups.length > 0 && (
            <Section title="Overdue follow-ups" icon={Clock}>
              <div className="space-y-1.5">
                {rep.overdue_followups.map((o, i) => (
                  <Link key={i} to={`/leads/${o.lead_id}`} className="flex items-center gap-2 p-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20">
                    <Clock size={14} className="text-amber-600" />
                    <span className="text-sm text-ink-700"><b className="text-ink-900">{o.lead}</b> · no follow-up in {o.days} days</span>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {/* attendance check-ins */}
          <Section title="Attendance & clock-in locations" icon={MapPin}>
            {rep.checkins.length === 0 ? <p className="text-sm text-ink-400">No check-ins this month.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                      <th className="pb-2 pr-4 font-semibold">Date</th>
                      <th className="pb-2 pr-4 font-semibold">In</th>
                      <th className="pb-2 pr-4 font-semibold">Out</th>
                      <th className="pb-2 pr-4 font-semibold">Location</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rep.checkins.map((c, i) => (
                      <tr key={i} className="border-t border-ink-100">
                        <td className="py-2 pr-4 whitespace-nowrap">{day(c.date)}</td>
                        <td className="py-2 pr-4 whitespace-nowrap">{dt(c.checkin)}</td>
                        <td className="py-2 pr-4 whitespace-nowrap">{dt(c.checkout)}</td>
                        <td className="py-2 pr-4">
                          {c.map ? <a href={c.map} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">📍 {c.address || "View on map"}</a> : <span className="text-ink-400">—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>
        </>
      )}
    </div>
  );
}
