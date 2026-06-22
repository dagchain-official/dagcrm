import { useState } from "react";
import RefSelect from "./RefSelect";

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function DataForm({ fields, initial, onSubmit, onCancel, submitting }) {
  const [form, setForm] = useState(() => ({ ...initial }));
  const [errors, setErrors] = useState({});
  const set = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }));
    setErrors((e) => (e[k] ? { ...e, [k]: undefined } : e));
  };

  const validate = () => {
    const errs = {};
    for (const f of fields) {
      const v = form[f.key];
      if (f.required && (v === "" || v == null)) errs[f.key] = `${f.label} is required`;
      else if (f.type === "email" && v && !emailRe.test(v)) errs[f.key] = "Enter a valid email";
      else if (f.type === "number" && v !== "" && v != null && isNaN(Number(v))) errs[f.key] = "Must be a number";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const submit = (e) => {
    e.preventDefault();
    if (validate()) onSubmit(form);
  };

  const inputCls = (f) => `input ${errors[f.key] ? "!border-rose-400 !ring-2 !ring-rose-100" : ""}`;

  return (
    <form id="data-form" onSubmit={submit} className="space-y-4" noValidate>
      <div className="grid sm:grid-cols-2 gap-4">
        {fields.map((f) => (
          <div key={f.key} className={f.type === "textarea" ? "sm:col-span-2" : ""}>
            <label className="label">
              {f.label} {f.required && <span className="text-rose-500">*</span>}
            </label>
            {f.type === "ref" ? (
              <RefSelect field={f} value={form[f.key]} onChange={(v) => set(f.key, v)} />
            ) : f.type === "select" ? (
              <select className={inputCls(f)} value={form[f.key] ?? ""} onChange={(e) => set(f.key, e.target.value)}>
                <option value="">— select —</option>
                {f.options.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            ) : f.type === "textarea" ? (
              <textarea className={`${inputCls(f)} min-h-[90px]`} value={form[f.key] ?? ""} onChange={(e) => set(f.key, e.target.value)} />
            ) : (
              <input
                className={inputCls(f)}
                type={f.type === "number" ? "text" : f.type || "text"}
                value={form[f.key] ?? ""}
                onChange={(e) => set(f.key, e.target.value)}
              />
            )}
            {errors[f.key] && <p className="text-xs text-rose-500 mt-1">{errors[f.key]}</p>}
          </div>
        ))}
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? "Saving…" : "Save"}
        </button>
      </div>
    </form>
  );
}
