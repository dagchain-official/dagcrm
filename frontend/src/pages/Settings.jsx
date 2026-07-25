import { useEffect, useState } from "react";
import { Settings2, Save } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";
import { useToast } from "../context/ToastContext";

// Company-wide settings (the Excel "Settings" list). Admin-editable.
const FIELDS = [
  { key: "currency", label: "Currency", type: "text", hint: "e.g. USD, AED, INR — shown across money figures" },
  { key: "workdays_per_month", label: "Workdays / month", type: "number", hint: "Used for CTC / payroll working-day calc" },
  { key: "default_incentive_rate", label: "Default incentive rate", type: "number", step: "0.001", hint: "Fallback % (as a fraction, e.g. 0.03 = 3%)" },
  { key: "training_pass_mark", label: "Training pass mark", type: "number", step: "0.01", hint: "Fraction, e.g. 0.8 = 80% (used once Training is added)" },
  { key: "first_contact_sla_min", label: "First-contact SLA (min)", type: "number", hint: "Minutes to first response (used once SLA is tracked)" },
  { key: "company_health_target", label: "Company health target", type: "number", step: "0.01", hint: "Fraction, e.g. 0.85 — the CEO dashboard's Healthy line" },
];

export default function Settings() {
  const toast = useToast();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/reports/settings/")
    .then((r) => { setD(r.data); setForm(r.data); setErr(""); })
    .catch(() => setErr("You don't have access to settings."));
  useEffect(() => { load(); }, []);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading settings…" />;

  const canEdit = d.can_edit;
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const save = () => {
    setSaving(true);
    api.put("/reports/settings/", form)
      .then(({ data }) => { setD(data); setForm(data); toast.success("Settings saved"); })
      .catch(() => toast.error("Could not save settings"))
      .finally(() => setSaving(false));
  };

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Settings2 className="text-brand-600" /> Settings
        </h1>
        <p className="text-sm text-ink-400">Company-wide configuration. {canEdit ? "Changes apply everywhere the value is used." : "View only — ask an administrator to change these."}</p>
      </div>

      <div className="card p-5 divide-y divide-ink-50">
        {FIELDS.map((f) => (
          <div key={f.key} className="flex flex-wrap items-center gap-3 py-3">
            <div className="flex-1 min-w-[200px]">
              <p className="font-medium text-ink-800">{f.label}</p>
              <p className="text-xs text-ink-400">{f.hint}</p>
            </div>
            <input className="input !w-40" type={f.type} step={f.step} disabled={!canEdit}
              value={form[f.key] ?? ""} onChange={set(f.key)} />
          </div>
        ))}
      </div>

      {canEdit && (
        <div className="flex justify-end">
          <button className="btn-primary inline-flex items-center gap-1.5" disabled={saving} onClick={save}>
            <Save size={16} /> {saving ? "Saving…" : "Save settings"}
          </button>
        </div>
      )}
    </div>
  );
}
