import { useState, useEffect } from "react";
import { Plus, Trash2, Save, X, Wand2 } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";

const OPS = [
  { value: "gt", label: ">" }, { value: "gte", label: "≥" }, { value: "lt", label: "<" },
  { value: "lte", label: "≤" }, { value: "eq", label: "=" }, { value: "between", label: "between" },
];
const PAYOUTS = [
  { value: "percent", label: "Percent of" }, { value: "flat", label: "Flat amount" },
  { value: "per_unit", label: "Per unit of" },
];
const newCond = () => ({ left: "revenue", operator: "gt", right_type: "constant", right_value: 0, right_value2: null, right_variable: "cost", right_factor: 1 });
const newRule = () => ({ name: "", match: "all", payout_type: "percent", payout_on: "revenue", payout_value: 0, status: "active", conditions: [newCond()] });

export default function FormulaBuilder() {
  const [vars, setVars] = useState([]);
  const [rules, setRules] = useState(null);
  const [form, setForm] = useState(null);          // null = not editing
  const [saving, setSaving] = useState(false);

  const varLabel = (k) => vars.find((v) => v.key === k)?.label || k;

  const load = () => api.get("/formula-rules/").then((r) => setRules(r.data.results || r.data));
  useEffect(() => {
    api.get("/reports/formula-variables/").then((r) => setVars(r.data.variables)).catch(() => {});
    load();
  }, []);

  const preview = (f) => {
    const parts = f.conditions.map((c) => {
      const left = varLabel(c.left);
      let rhs;
      if (c.operator === "between") rhs = `${c.right_value}–${c.right_value2 ?? c.right_value}`;
      else if (c.right_type === "variable") rhs = varLabel(c.right_variable) + (Number(c.right_factor) !== 1 ? ` × ${c.right_factor}` : "");
      else rhs = `${c.right_value}`;
      return `${left} ${OPS.find((o) => o.value === c.operator)?.label} ${rhs}`;
    });
    const cond = parts.join(f.match === "all" ? " AND " : " OR ") || "always";
    const act = f.payout_type === "percent" ? `${f.payout_value}% of ${varLabel(f.payout_on)}`
      : f.payout_type === "per_unit" ? `${f.payout_value} per ${varLabel(f.payout_on)}` : `$${f.payout_value} flat`;
    return `IF ${cond} → ${act}`;
  };

  const setCond = (i, patch) => setForm((f) => ({ ...f, conditions: f.conditions.map((c, j) => (j === i ? { ...c, ...patch } : c)) }));
  const addCond = () => setForm((f) => ({ ...f, conditions: [...f.conditions, newCond()] }));
  const delCond = (i) => setForm((f) => ({ ...f, conditions: f.conditions.filter((_, j) => j !== i) }));

  const save = async () => {
    setSaving(true);
    try {
      const payload = { ...form, payout_on: form.payout_type === "flat" ? "" : form.payout_on };
      if (form.id) await api.put(`/formula-rules/${form.id}/`, payload);
      else await api.post("/formula-rules/", payload);
      setForm(null); load();
    } catch (e) { alert("Save failed: " + JSON.stringify(e.response?.data || e.message)); }
    finally { setSaving(false); }
  };
  const remove = async (id) => { if (confirm("Delete this rule?")) { await api.delete(`/formula-rules/${id}/`); load(); } };

  if (!rules) return <Spinner label="Loading rules…" />;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><Wand2 className="text-brand-600" /> Formula Builder</h1>
          <p className="text-sm text-ink-400">Define incentive rules — no code. Variables come from the live engines.</p>
        </div>
        {!form && <button onClick={() => setForm(newRule())} className="btn-primary flex items-center gap-1.5"><Plus size={16} /> New rule</button>}
      </div>

      {form && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center gap-2">
            <input className="input flex-1" placeholder="Rule name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <select className="input !w-auto" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="active">Active</option><option value="inactive">Inactive</option>
            </select>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-ink-500 uppercase">When</span>
              <select className="input !w-auto !py-1 text-xs" value={form.match} onChange={(e) => setForm({ ...form, match: e.target.value })}>
                <option value="all">match ALL (AND)</option><option value="any">match ANY (OR)</option>
              </select>
            </div>
            <div className="space-y-2">
              {form.conditions.map((c, i) => (
                <div key={i} className="flex flex-wrap items-center gap-2 bg-ink-50/60 rounded-lg p-2">
                  <select className="input !w-auto" value={c.left} onChange={(e) => setCond(i, { left: e.target.value })}>
                    {vars.map((v) => <option key={v.key} value={v.key}>{v.label}</option>)}
                  </select>
                  <select className="input !w-auto" value={c.operator} onChange={(e) => setCond(i, { operator: e.target.value })}>
                    {OPS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  {c.operator === "between" ? (
                    <>
                      <input type="number" className="input !w-24" value={c.right_value} onChange={(e) => setCond(i, { right_value: e.target.value })} />
                      <span className="text-ink-400 text-sm">and</span>
                      <input type="number" className="input !w-24" value={c.right_value2 ?? ""} onChange={(e) => setCond(i, { right_value2: e.target.value })} />
                    </>
                  ) : (
                    <>
                      <select className="input !w-auto" value={c.right_type} onChange={(e) => setCond(i, { right_type: e.target.value })}>
                        <option value="constant">a number</option><option value="variable">a variable</option>
                      </select>
                      {c.right_type === "constant" ? (
                        <input type="number" className="input !w-28" value={c.right_value} onChange={(e) => setCond(i, { right_value: e.target.value })} />
                      ) : (
                        <>
                          <select className="input !w-auto" value={c.right_variable} onChange={(e) => setCond(i, { right_variable: e.target.value })}>
                            {vars.map((v) => <option key={v.key} value={v.key}>{v.label}</option>)}
                          </select>
                          <span className="text-ink-400 text-sm">×</span>
                          <input type="number" className="input !w-20" value={c.right_factor} onChange={(e) => setCond(i, { right_factor: e.target.value })} />
                        </>
                      )}
                    </>
                  )}
                  {form.conditions.length > 1 && <button onClick={() => delCond(i)} className="text-rose-400 hover:text-rose-600"><Trash2 size={16} /></button>}
                </div>
              ))}
              <button onClick={addCond} className="text-xs text-brand-600 font-semibold flex items-center gap-1"><Plus size={13} /> add condition</button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-ink-500 uppercase">Then pay</span>
            <select className="input !w-auto" value={form.payout_type} onChange={(e) => setForm({ ...form, payout_type: e.target.value })}>
              {PAYOUTS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
            <input type="number" className="input !w-28" value={form.payout_value} onChange={(e) => setForm({ ...form, payout_value: e.target.value })} />
            {form.payout_type !== "flat" && (
              <select className="input !w-auto" value={form.payout_on} onChange={(e) => setForm({ ...form, payout_on: e.target.value })}>
                {vars.map((v) => <option key={v.key} value={v.key}>{v.label}</option>)}
              </select>
            )}
          </div>

          <div className="bg-brand-50 text-brand-800 text-sm rounded-lg px-3 py-2 font-medium">{preview(form)}</div>

          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving || !form.name} className="btn-primary flex items-center gap-1.5 disabled:opacity-50"><Save size={15} /> {saving ? "Saving…" : "Save rule"}</button>
            <button onClick={() => setForm(null)} className="px-3 py-2 text-sm text-ink-500 flex items-center gap-1"><X size={15} /> Cancel</button>
          </div>
        </div>
      )}

      <div className="card p-5">
        {rules.length ? (
          <div className="space-y-1">
            {rules.map((r) => (
              <div key={r.id} className="flex items-center gap-3 py-2.5 border-b border-ink-100 last:border-0">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-ink-800">{r.name} {r.status === "inactive" && <span className="text-[10px] text-ink-400">(inactive)</span>}</p>
                  <p className="text-[12px] text-ink-500">{r.label}</p>
                </div>
                <button onClick={() => setForm({ ...r, conditions: r.conditions.length ? r.conditions : [newCond()] })} className="text-xs text-brand-600 font-semibold">Edit</button>
                <button onClick={() => remove(r.id)} className="text-rose-400 hover:text-rose-600"><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        ) : <EmptyState title="No rules yet" hint="Click “New rule” to build your first incentive formula." />}
      </div>
    </div>
  );
}
