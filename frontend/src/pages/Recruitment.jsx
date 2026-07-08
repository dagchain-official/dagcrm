import { useEffect, useState } from "react";
import {
  Users2, Plus, ArrowLeft, Copy, Link2, CheckCircle2, XCircle, Star,
  Download, Percent, RefreshCw, Briefcase,
} from "lucide-react";
import api from "../api/client";
import usePolling from "../hooks/usePolling";
import { Spinner, EmptyState, Modal, Badge } from "../components/ui";
import { useToast } from "../context/ToastContext";

const BLANK = {
  title: "", role_name: "", business: "", department: "", location: "",
  experience: "", description: "", required_skills: "", min_match_pct: 60, status: "open",
};
const STATUS_MAP = {
  applied: "bg-ink-100 text-ink-600", shortlisted: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-600", hired: "bg-violet-100 text-violet-700",
  open: "bg-emerald-100 text-emerald-700", closed: "bg-ink-100 text-ink-500",
};

function MatchBar({ pct }) {
  const tone = pct >= 75 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2 min-w-[130px]">
      <div className="flex-1 h-2 rounded-full bg-ink-100 overflow-hidden">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-bold tabular-nums w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function Recruitment() {
  const toast = useToast();
  const [jobs, setJobs] = useState(null);
  const [sel, setSel] = useState(null);          // selected job (detail view)
  const [cands, setCands] = useState([]);
  const [editing, setEditing] = useState(null);  // job form object
  const [saving, setSaving] = useState(false);
  const [refs, setRefs] = useState({ businesses: [], departments: [] });

  const loadJobs = () => api.get("/job-postings/").then((r) => setJobs(r.data?.results || r.data || [])).catch(() => setJobs([]));
  const loadCands = (jobId) => api.get("/candidates/", { params: { job: jobId } })
    .then((r) => setCands(r.data?.results || r.data || [])).catch(() => setCands([]));

  useEffect(() => {
    Promise.all([api.get("/businesses/"), api.get("/departments/")]).then(([b, dp]) => {
      setRefs({ businesses: b.data?.results || b.data || [], departments: dp.data?.results || dp.data || [] });
    }).catch(() => {});
  }, []);
  // live: new applications (auto-scored) show up without a manual refresh
  usePolling(loadJobs, 5000, []);
  usePolling(() => { if (sel) loadCands(sel.id); }, 4000, [sel]);

  const openNew = () => setEditing({ ...BLANK });
  const openEdit = (j) => setEditing({ ...j, business: j.business || "", department: j.department || "" });
  const set = (k) => (e) => setEditing((f) => ({ ...f, [k]: e.target.value }));

  const saveJob = async () => {
    if (!editing.title) return toast.error("Title zaroori hai");
    setSaving(true);
    try {
      const body = { ...editing, business: editing.business || null, department: editing.department || null };
      const { data } = editing.id
        ? await api.patch(`/job-postings/${editing.id}/`, body)
        : await api.post("/job-postings/", body);
      setEditing(null);
      await loadJobs();
      if (sel?.id === data.id) setSel(data);
      toast.success("Job saved");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  const applyUrl = (j) => `${window.location.origin}/apply/${j.public_token}`;
  const copyLink = (j) => { navigator.clipboard?.writeText(applyUrl(j)); toast.info("Apply link copied"); };

  const setStatus = async (c, status) => {
    await api.post(`/candidates/${c.id}/set_status/`, { status });
    loadCands(sel.id); loadJobs();
  };
  const rescoreAll = async () => {
    await Promise.all(cands.map((c) => api.post(`/candidates/${c.id}/rescore/`)));
    loadCands(sel.id); loadJobs(); toast.success("Re-scored against current skills");
  };

  if (jobs === null) return <Spinner label="Loading recruitment…" />;

  // ---------- JOB DETAIL (candidates) ----------
  if (sel) {
    const job = jobs.find((j) => j.id === sel.id) || sel;
    return (
      <div className="space-y-5">
        <button onClick={() => setSel(null)} className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink-500 hover:text-ink-800">
          <ArrowLeft size={16} /> All jobs
        </button>

        <div className="card p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-extrabold text-ink-900">{job.title}</h1>
              <p className="text-sm text-ink-500 mt-1">
                {job.role_name || "—"}{job.business_name ? ` · ${job.business_name}` : ""}{job.location ? ` · ${job.location}` : ""}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <span className="badge inline-flex items-center gap-1 bg-brand-50 text-brand-700"><Percent size={12} /> Shortlist ≥ {job.min_match_pct}%</span>
                <Badge value={job.status} map={STATUS_MAP} />
                <button className="btn-ghost text-sm border border-ink-200" onClick={() => openEdit(job)}>Edit job</button>
                <button className="btn-ghost text-sm border border-ink-200" onClick={rescoreAll}><RefreshCw size={14} /> Re-score</button>
              </div>
            </div>
            <div className="min-w-[240px]">
              <label className="label">Public apply link (ad me daalo)</label>
              <div className="flex gap-2">
                <input readOnly value={applyUrl(job)} onFocus={(e) => e.target.select()} className="input font-mono text-xs" />
                <button className="chip !py-2" onClick={() => copyLink(job)}><Copy size={14} /></button>
              </div>
            </div>
          </div>
          {job.required_skills && (
            <div className="mt-4">
              <label className="label">Required skills</label>
              <div className="flex flex-wrap gap-1.5">
                {job.required_skills.split(/[,\n;]+/).map((s) => s.trim()).filter(Boolean).map((s, i) => (
                  <span key={i} className="chip !py-1 !text-xs">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="p-4 border-b border-ink-100 flex items-center justify-between">
            <h3 className="font-bold text-ink-900">Candidates ({cands.length})</h3>
            <p className="text-xs text-ink-400">Match % ke hisaab se sorted</p>
          </div>
          {cands.length === 0 ? (
            <EmptyState title="Abhi koi candidate nahi" hint="Apply link share karo — applications yahaँ auto-score hokar aayengi." />
          ) : (
            <div className="divide-y divide-ink-100">
              {cands.map((c) => (
                <div key={c.id} className="p-4 flex flex-wrap items-center gap-4 hover:bg-ink-50/50">
                  <div className="min-w-[180px] flex-1">
                    <p className="font-semibold text-ink-800">{c.name}</p>
                    <p className="text-xs text-ink-400">{c.email || "—"}{c.phone ? ` · ${c.phone}` : ""}</p>
                  </div>
                  <MatchBar pct={c.match_pct} />
                  <div className="hidden lg:block min-w-[200px] flex-1">
                    <div className="flex flex-wrap gap-1">
                      {(c.matched_skills || []).slice(0, 6).map((s, i) => (
                        <span key={i} className="text-[11px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">{s}</span>
                      ))}
                      {(c.missing_skills || []).slice(0, 4).map((s, i) => (
                        <span key={`m${i}`} className="text-[11px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-500 line-through">{s}</span>
                      ))}
                    </div>
                  </div>
                  <Badge value={c.status} map={STATUS_MAP} />
                  <div className="flex items-center gap-1">
                    {c.resume_url && <a href={c.resume_url} target="_blank" rel="noreferrer" className="btn-ghost p-2 text-brand-600" title="Resume"><Download size={16} /></a>}
                    <button className="btn-ghost p-2 text-emerald-600" title="Shortlist" onClick={() => setStatus(c, "shortlisted")}><Star size={16} /></button>
                    <button className="btn-ghost p-2 text-violet-600" title="Hire" onClick={() => setStatus(c, "hired")}><CheckCircle2 size={16} /></button>
                    <button className="btn-ghost p-2 text-rose-500" title="Reject" onClick={() => setStatus(c, "rejected")}><XCircle size={16} /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <JobModal {...{ editing, setEditing, set, saveJob, saving, refs }} />
      </div>
    );
  }

  // ---------- JOB LIST ----------
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Users2 className="text-brand-600" /> Recruitment</h1>
          <p className="text-sm text-ink-400">Job ad chalao → candidate resume daale → system auto match % nikaal ke shortlist kare</p>
        </div>
        <button className="btn-primary" onClick={openNew}><Plus size={16} /> New Job</button>
      </div>

      {jobs.length === 0 && (
        <div className="card p-10 text-center">
          <p className="text-ink-500 font-semibold">Abhi koi job posting nahi.</p>
          <button className="btn-primary mt-4 mx-auto" onClick={openNew}><Plus size={16} /> New Job</button>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {jobs.map((j) => (
          <button key={j.id} onClick={() => setSel(j)} className="card p-5 text-left hover:shadow-soft transition">
            <div className="flex items-start justify-between">
              <div className="grid place-items-center w-11 h-11 rounded-2xl bg-brand-100 text-brand-600"><Briefcase size={20} /></div>
              <Badge value={j.status} map={STATUS_MAP} />
            </div>
            <h3 className="font-bold text-ink-900 mt-3">{j.title}</h3>
            <p className="text-xs text-ink-400">{j.role_name || "—"}{j.business_name ? ` · ${j.business_name}` : ""}</p>
            <div className="flex items-center gap-4 mt-3 text-sm">
              <span><b className="text-ink-900">{j.candidate_count}</b> <span className="text-ink-400">applied</span></span>
              <span><b className="text-emerald-600">{j.shortlisted_count}</b> <span className="text-ink-400">shortlisted</span></span>
            </div>
            <p className="text-[11px] text-ink-400 mt-2 inline-flex items-center gap-1"><Link2 size={11} /> shortlist ≥ {j.min_match_pct}%</p>
          </button>
        ))}
      </div>

      <JobModal {...{ editing, setEditing, set, saveJob, saving, refs }} />
    </div>
  );
}

function JobModal({ editing, setEditing, set, saveJob, saving, refs }) {
  return (
    <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Edit job" : "New job posting"} size="lg"
      footer={<>
        <button className="btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
        <button className="btn-primary" disabled={saving} onClick={saveJob}>{saving ? "Saving…" : "Save job"}</button>
      </>}>
      {editing && (
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2"><label className="label">Job title</label><input className="input" placeholder="Sales Executive" value={editing.title} onChange={set("title")} /></div>
          <div><label className="label">Role</label><input className="input" placeholder="Sales" value={editing.role_name} onChange={set("role_name")} /></div>
          <div><label className="label">Location</label><input className="input" placeholder="Remote / Delhi" value={editing.location} onChange={set("location")} /></div>
          <div><label className="label">Business</label>
            <select className="input" value={editing.business} onChange={set("business")}>
              <option value="">—</option>
              {refs.businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div><label className="label">Department</label>
            <select className="input" value={editing.department} onChange={set("department")}>
              <option value="">—</option>
              {refs.departments.map((d) => <option key={d.id} value={d.id}>{d.department_name}</option>)}
            </select>
          </div>
          <div><label className="label">Experience</label><input className="input" placeholder="2-4 years" value={editing.experience} onChange={set("experience")} /></div>
          <div><label className="label">Shortlist threshold (%)</label><input className="input" type="number" min="0" max="100" value={editing.min_match_pct} onChange={set("min_match_pct")} /></div>
          <div className="sm:col-span-2">
            <label className="label">Required skills <span className="text-ink-400 font-normal">(comma se alag — inhi se match hoga)</span></label>
            <textarea className="input min-h-[70px]" placeholder="React, Node.js, MongoDB, 3 years, English" value={editing.required_skills} onChange={set("required_skills")} />
          </div>
          <div className="sm:col-span-2"><label className="label">Description</label><textarea className="input min-h-[80px]" placeholder="Role ke baare me…" value={editing.description} onChange={set("description")} /></div>
          <div><label className="label">Status</label>
            <select className="input" value={editing.status} onChange={set("status")}>
              <option value="open">Open</option><option value="closed">Closed</option>
            </select>
          </div>
        </div>
      )}
    </Modal>
  );
}
