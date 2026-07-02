import { useEffect, useState } from "react";
import { Crosshair, Users, Building2, User } from "lucide-react";
import api from "../api/client";
import RefSelect from "../components/RefSelect";
import { Spinner } from "../components/ui";
import { useToast } from "../context/ToastContext";

const now = new Date();
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const SCOPES = [
  { key: "user", label: "Individual", icon: User, hint: "One employee's CTC" },
  { key: "team", label: "Team", icon: Users, hint: "Whole team's CTC" },
  { key: "business", label: "Business", icon: Building2, hint: "A head's entire org CTC" },
];

export default function AssignTarget() {
  const toast = useToast();
  const [scope, setScope] = useState("user");
  const [id, setId] = useState("");
  const [multiplier, setMultiplier] = useState(2);
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [name, setName] = useState("");
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const refField = scope === "team"
    ? { ref: "teams", labelKey: "name", label: "Team" }
    : { ref: "users", labelKey: "name", label: scope === "business" ? "Business Head" : "Employee" };

  useEffect(() => { setId(""); setPreview(null); }, [scope]);

  useEffect(() => {
    if (!id) { setPreview(null); return; }
    setLoading(true);
    api.get("/reports/ctc-preview/", { params: { scope, id, month, year, multiplier } })
      .then(({ data }) => setPreview(data)).catch(() => setPreview(null)).finally(() => setLoading(false));
  }, [scope, id, month, year, multiplier]);

  const assign = async () => {
    if (!id) return toast.error("Select who to assign the target to");
    setSaving(true);
    try {
      const { data } = await api.post("/reports/assign-target/",
        { scope, id, multiplier, month, year, name });
      toast.success(`Target assigned: ${money(data.value)} across ${data.assignees} people`);
      setId(""); setPreview(null); setName("");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Assign failed");
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Crosshair className="text-brand-600" /> Assign Target
        </h1>
        <p className="text-sm text-ink-400">Target = CTC × Multiplier. Pick individual / team / business — CTC auto-calculates.</p>
      </div>

      {/* scope picker */}
      <div className="grid grid-cols-3 gap-3">
        {SCOPES.map((s) => (
          <button key={s.key} onClick={() => setScope(s.key)}
            className={`card p-4 text-left transition ${scope === s.key ? "!border-brand-400 bg-brand-50" : "hover:bg-ink-50"}`}>
            <s.icon size={20} className={scope === s.key ? "text-brand-600" : "text-ink-400"} />
            <p className="font-bold text-ink-800 mt-2">{s.label}</p>
            <p className="text-xs text-ink-400">{s.hint}</p>
          </button>
        ))}
      </div>

      <div className="card p-5 space-y-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">{refField.label}</label>
            <RefSelect field={refField} value={id} onChange={setId} />
          </div>
          <div>
            <label className="label">Target name (optional)</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Auto-named if blank" />
          </div>
          <div>
            <label className="label">Multiplier (Target = CTC × this)</label>
            <input className="input" type="number" step="0.1" value={multiplier} onChange={(e) => setMultiplier(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">Month</label>
              <select className="input" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
                {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Year</label>
              <select className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>
                {[year - 1, year, year + 1].map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* CTC preview */}
        {loading ? <Spinner /> : preview && id && (
          <div className="rounded-xl border border-ink-100 bg-ink-50/60 p-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div><p className="text-xl font-extrabold text-ink-800 tabular-nums">{money(preview.ctc)}</p><p className="text-xs text-ink-400">Total CTC ({preview.count} {preview.count === 1 ? "person" : "people"})</p></div>
              <div><p className="text-xl font-extrabold text-ink-600 tabular-nums">× {preview.multiplier}</p><p className="text-xs text-ink-400">Multiplier</p></div>
              <div><p className="text-2xl font-extrabold text-brand-600 tabular-nums">{money(preview.suggested_target)}</p><p className="text-xs text-ink-400">Suggested Target</p></div>
            </div>
            {preview.members?.length > 1 && (
              <div className="mt-3 pt-3 border-t border-ink-100 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-500">
                {preview.members.map((m) => <span key={m.user_id}>{m.name}: <b className="text-ink-700">{money(m.ctc)}</b></span>)}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <button className="btn-primary" disabled={saving || !id} onClick={assign}>
            {saving ? "Assigning…" : "Assign Target"}
          </button>
        </div>
      </div>
    </div>
  );
}
