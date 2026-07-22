import { useEffect, useState } from "react";
import { Crosshair, Users, Building2, User, X, Plus } from "lucide-react";
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
  const [incType, setIncType] = useState("");   // "" | percentage | fixed | slab
  const [incValue, setIncValue] = useState("");
  const [slabs, setSlabs] = useState([]);       // attainment tiers when type = slab
  const [dedPct, setDedPct] = useState("");     // deduction % of target if missed
  const [overPct, setOverPct] = useState("");   // increment % on over-achievement

  // load the current global slabs into the editor when "slab" is picked
  useEffect(() => {
    if (incType !== "slab") return;
    api.get("/incentive-slabs/").then((r) => {
      const rows = (r.data.results || r.data || [])
        .map((s) => ({ min_pct: s.min_pct, max_pct: s.max_pct ?? "", incentive_pct: s.incentive_pct }));
      setSlabs(rows.length ? rows : [
        { min_pct: 0, max_pct: 100, incentive_pct: 0 },
        { min_pct: 100, max_pct: "", incentive_pct: 10 },
      ]);
    }).catch(() => setSlabs([{ min_pct: 100, max_pct: "", incentive_pct: 10 }]));
  }, [incType]);
  const setSlab = (i, k, v) => setSlabs((s) => s.map((r, x) => (x === i ? { ...r, [k]: v } : r)));

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
      const payload = { scope, id, multiplier, month, year, name };
      if (incType) payload.incentive = {
        type: incType,
        value: incType === "slab" ? 0 : Number(incValue || 0),
        slabs: incType === "slab" ? slabs : undefined,
        deduction_pct: Number(dedPct || 0),
        over_pct: Number(overPct || 0),
      };
      const { data } = await api.post("/reports/assign-target/", payload);
      let msg = `Target assigned: ${money(data.value)} across ${data.assignees} people`;
      if (data.incentive?.employees) msg += ` · incentive plan set for ${data.incentive.employees}`;
      toast.success(msg);
      setId(""); setPreview(null); setName(""); setIncType(""); setIncValue(""); setDedPct(""); setOverPct("");
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
            className={`card p-4 text-left transition ${scope === s.key ? "!border-brand-400 bg-brand-50 dark:bg-brand-500/15" : "hover:bg-ink-50"}`}>
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

        {/* optional incentive — set alongside the target */}
        <div className="rounded-xl border border-ink-100 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-bold text-ink-800">Set incentive (optional)</p>
            {incType && <button className="text-xs text-ink-400 hover:text-rose-500" onClick={() => { setIncType(""); setIncValue(""); }}>Clear</button>}
          </div>
          <div className="flex flex-wrap gap-2">
            {[["percentage", "% of target"], ["fixed", "Fixed amount"], ["slab", "Slab (attainment)"]].map(([v, label]) => (
              <button key={v} onClick={() => setIncType(v)}
                className={`chip !py-2 ${incType === v ? "!bg-brand-50 !text-brand-700 border border-brand-300" : ""}`}>
                {label}
              </button>
            ))}
          </div>
          {(incType === "percentage" || incType === "fixed") && (
            <div className="flex items-center gap-2">
              <input className="input w-40" type="number" step={incType === "percentage" ? "0.5" : "100"}
                placeholder={incType === "percentage" ? "e.g. 10" : "e.g. 5000"}
                value={incValue} onChange={(e) => setIncValue(e.target.value)} />
              <span className="text-sm text-ink-500">{incType === "percentage" ? "% of each person's target" : "$ per person"}</span>
            </div>
          )}
          {incType === "percentage" && preview && incValue && (
            <p className="text-xs text-ink-500">≈ {money(preview.suggested_target * Number(incValue) / 100)} total incentive on this target</p>
          )}
          {incType === "slab" && (
            <div className="space-y-2">
              <p className="text-xs text-ink-500">Define attainment tiers: if achievement falls in a range, that % of revenue is the incentive. (Blank “To” = ∞.)</p>
              <div className="space-y-1.5">
                {slabs.map((s, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs">
                    <span className="text-ink-400">From</span>
                    <input className="input w-16 !py-1.5 !text-xs" type="number" value={s.min_pct} onChange={(e) => setSlab(i, "min_pct", e.target.value)} />
                    <span className="text-ink-400">% to</span>
                    <input className="input w-16 !py-1.5 !text-xs" type="number" placeholder="∞" value={s.max_pct} onChange={(e) => setSlab(i, "max_pct", e.target.value)} />
                    <span className="text-ink-400">% →</span>
                    <input className="input w-16 !py-1.5 !text-xs" type="number" value={s.incentive_pct} onChange={(e) => setSlab(i, "incentive_pct", e.target.value)} />
                    <span className="text-ink-400">% incentive</span>
                    <button className="text-ink-400 hover:text-rose-500 ml-1" onClick={() => setSlabs(slabs.filter((_, x) => x !== i))}><X size={13} /></button>
                  </div>
                ))}
              </div>
              <button className="text-xs text-brand-600 font-semibold inline-flex items-center gap-1"
                onClick={() => setSlabs([...slabs, { min_pct: "", max_pct: "", incentive_pct: "" }])}>
                <Plus size={12} /> Add tier
              </button>
              <p className="text-[11px] text-ink-400">Saved as this employee/team's slab (priority over the global one); the real payout computes from actual attainment.</p>
            </div>
          )}

          {/* deduction on miss + increment on over-achievement (apply to all types) */}
          {incType && (
            <div className="grid sm:grid-cols-2 gap-3 pt-3 border-t border-ink-100">
              <div>
                <label className="label text-xs">Deduction if target missed <span className="text-ink-400 font-normal">(optional)</span></label>
                <div className="flex items-center gap-2">
                  <input className="input w-24 !py-1.5" type="number" placeholder="0" value={dedPct} onChange={(e) => setDedPct(e.target.value)} />
                  <span className="text-xs text-ink-500">% of target</span>
                </div>
              </div>
              <div>
                <label className="label text-xs">Increment on over-achievement <span className="text-ink-400 font-normal">(optional)</span></label>
                <div className="flex items-center gap-2">
                  <input className="input w-24 !py-1.5" type="number" placeholder="0" value={overPct} onChange={(e) => setOverPct(e.target.value)} />
                  <span className="text-xs text-ink-500">% of amount above target</span>
                </div>
              </div>
            </div>
          )}

          {incType && (
            <p className="text-[11px] text-brand-600 bg-brand-50 rounded-lg px-3 py-2">
              This plan gets <b>priority</b> over the global incentive section. Payout computes from actual attainment: <b>met</b> → incentive {overPct ? `+ ${overPct}% on extra` : ""}, <b>missed</b> → {dedPct ? `−${dedPct}% of target` : "no deduction"}.
            </p>
          )}
        </div>

        <div className="flex justify-end">
          <button className="btn-primary" disabled={saving || !id} onClick={assign}>
            {saving ? "Assigning…" : "Assign Target"}
          </button>
        </div>
      </div>
    </div>
  );
}
