import { useEffect, useState } from "react";
import { CalendarOff, Plus } from "lucide-react";
import api from "../api/client";
import { Badge, Spinner, EmptyState, Modal } from "../components/ui";
import { STATUS_COLORS } from "../config/resources";

const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

export default function MyLeaves() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ leave_type: "", start_date: "", end_date: "", reason: "" });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const load = () => api.get("/my-leaves/").then((r) => setData(r.data)).catch(() => setData({ leaves: [], leave_types: [] }));
  useEffect(() => { load(); }, []);

  const apply = async (e) => {
    e.preventDefault();
    setErr("");
    if (!form.start_date || !form.end_date) return setErr("Start and end dates are required.");
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.leave_type) delete payload.leave_type;
      await api.post("/my-leaves/", payload);
      setOpen(false);
      setForm({ leave_type: "", start_date: "", end_date: "", reason: "" });
      load();
    } catch (e2) {
      setErr(e2.response?.data?.detail || "Failed to apply.");
    } finally {
      setSaving(false);
    }
  };

  if (!data) return <Spinner label="Loading your leaves…" />;

  const pending = data.leaves.filter((l) => l.status === "pending").length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900">My Leaves</h1>
          <p className="text-sm text-ink-400">Apply for leave & track your requests</p>
        </div>
        <button className="btn-primary" onClick={() => setOpen(true)}><Plus size={16} /> Apply for Leave</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[["Total", data.leaves.length, "text-ink-900"],
          ["Pending", pending, "text-amber-600"],
          ["Approved", data.leaves.filter((l) => l.status === "approved").length, "text-emerald-600"]].map(([l, v, c]) => (
          <div key={l} className="card p-5">
            <p className={`text-3xl font-extrabold tabular-nums ${c}`}>{v}</p>
            <p className="text-sm text-ink-400 mt-0.5">{l}</p>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <h3 className="font-bold text-ink-900 mb-4">Leave History</h3>
        {data.leaves.length === 0 ? (
          <EmptyState title="No leave requests yet" hint="Click “Apply for Leave” to submit one." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                  <th className="pb-3 px-4 font-semibold">Type</th>
                  <th className="pb-3 px-4 font-semibold">From</th>
                  <th className="pb-3 px-4 font-semibold">To</th>
                  <th className="pb-3 px-4 font-semibold">Reason</th>
                  <th className="pb-3 px-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.leaves.map((l) => (
                  <tr key={l.id} className="border-t border-ink-100">
                    <td className="py-3.5 px-4 text-ink-700">{l.leave_type_name || "—"}</td>
                    <td className="py-3.5 px-4 text-ink-700">{date(l.start_date)}</td>
                    <td className="py-3.5 px-4 text-ink-700">{date(l.end_date)}</td>
                    <td className="py-3.5 px-4 text-ink-500 max-w-[240px] truncate">{l.reason || "—"}</td>
                    <td className="py-3.5 px-4"><Badge value={l.status} map={STATUS_COLORS} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Apply for Leave"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="btn-primary" form="leave-form" disabled={saving}>{saving ? "Submitting…" : "Submit"}</button>
          </>
        }>
        <form id="leave-form" onSubmit={apply} className="space-y-4">
          {err && <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{err}</div>}
          <div>
            <label className="label">Leave Type</label>
            <select className="input" value={form.leave_type} onChange={(e) => setForm({ ...form, leave_type: e.target.value })}>
              <option value="">— select —</option>
              {data.leave_types.map((t) => <option key={t.id} value={t.id}>{t.leave_name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">From <span className="text-rose-500">*</span></label>
              <input className="input" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required />
            </div>
            <div>
              <label className="label">To <span className="text-rose-500">*</span></label>
              <input className="input" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} required />
            </div>
          </div>
          <div>
            <label className="label">Reason</label>
            <textarea className="input min-h-[80px]" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
          </div>
        </form>
      </Modal>
    </div>
  );
}
