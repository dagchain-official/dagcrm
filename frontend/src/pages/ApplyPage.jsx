import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Briefcase, MapPin, Clock, CheckCircle2, Upload, Loader2 } from "lucide-react";
import api from "../api/client";

export default function ApplyPage() {
  const { token } = useParams();
  const [job, setJob] = useState(undefined);   // undefined=loading, null=not found
  const [form, setForm] = useState({ name: "", email: "", phone: "", resume_text: "" });
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/jobs/apply/${token}/`)
      .then((r) => setJob(r.data))
      .catch(() => setJob(null));
  }, [token]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return setErr("Please enter your name.");
    setErr(""); setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("name", form.name);
      fd.append("email", form.email);
      fd.append("phone", form.phone);
      fd.append("resume_text", form.resume_text);
      if (file) fd.append("resume", file);
      const { data } = await api.post(`/jobs/apply/${token}/`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setDone(data.message || "Your application has been received.");
    } catch (e2) {
      setErr(e2.response?.data?.detail || "Could not submit. Please try again.");
    } finally { setSubmitting(false); }
  };

  const Shell = ({ children }) => (
    <div className="min-h-screen bg-ink-50 grid place-items-center p-4">
      <div className="w-full max-w-xl">{children}</div>
    </div>
  );

  if (job === undefined) return <Shell><div className="grid place-items-center py-20 text-ink-400"><Loader2 className="animate-spin" /></div></Shell>;
  if (job === null) return <Shell><div className="card p-10 text-center"><p className="text-lg font-bold text-ink-800">Job not available</p><p className="text-sm text-ink-400 mt-1">This position has closed, or the link is incorrect.</p></div></Shell>;

  if (done) return (
    <Shell>
      <div className="card p-10 text-center">
        <div className="grid place-items-center w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 mx-auto"><CheckCircle2 size={30} /></div>
        <h1 className="text-xl font-extrabold text-ink-900 mt-4">Application received 🎉</h1>
        <p className="text-sm text-ink-500 mt-2">{done}</p>
        <p className="text-xs text-ink-400 mt-4">Our team will review your profile and get in touch with you.</p>
      </div>
    </Shell>
  );

  return (
    <Shell>
      <div className="card p-7 space-y-5">
        <div>
          <div className="grid place-items-center w-12 h-12 rounded-2xl bg-brand-100 text-brand-600"><Briefcase size={22} /></div>
          <h1 className="text-2xl font-extrabold text-ink-900 mt-3">{job.title}</h1>
          <p className="text-sm text-ink-500 mt-1">{job.role_name}{job.business_name ? ` · ${job.business_name}` : ""}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-ink-500">
            {job.location && <span className="inline-flex items-center gap-1.5"><MapPin size={14} /> {job.location}</span>}
            {job.experience && <span className="inline-flex items-center gap-1.5"><Clock size={14} /> {job.experience}</span>}
          </div>
          {job.description && <p className="text-sm text-ink-600 mt-3 whitespace-pre-line">{job.description}</p>}
        </div>

        <form onSubmit={submit} className="space-y-4 border-t border-ink-100 pt-5">
          <h2 className="font-bold text-ink-900">Apply for this role</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div><label className="label">Full name *</label><input className="input" value={form.name} onChange={set("name")} /></div>
            <div><label className="label">Phone</label><input className="input" value={form.phone} onChange={set("phone")} /></div>
          </div>
          <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={set("email")} /></div>
          <div>
            <label className="label">Resume (PDF)</label>
            <label className="flex items-center gap-2 input cursor-pointer">
              <Upload size={16} className="text-ink-400" />
              <span className="text-sm text-ink-500 truncate">{file ? file.name : "Choose your resume file…"}</span>
              <input type="file" accept=".pdf,.txt,.doc,.docx" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </label>
          </div>
          <div>
            <label className="label">Or paste your resume / skills <span className="text-ink-400 font-normal">(optional)</span></label>
            <textarea className="input min-h-[90px]" placeholder="Paste your skills and experience here…" value={form.resume_text} onChange={set("resume_text")} />
          </div>
          {err && <p className="text-sm text-rose-600 bg-rose-50 rounded-lg px-3 py-2">{err}</p>}
          <button type="submit" disabled={submitting} className="btn-primary w-full justify-center">
            {submitting ? <><Loader2 size={16} className="animate-spin" /> Submitting…</> : "Submit application"}
          </button>
        </form>
      </div>
      <p className="text-center text-xs text-ink-400 mt-3">Powered by DAGOS CRM</p>
    </Shell>
  );
}
