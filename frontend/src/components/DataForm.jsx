import { useEffect, useRef, useState } from "react";
import RefSelect from "./RefSelect";
import CreatableSelect from "./CreatableSelect";
import api from "../api/client";

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function DataForm({ fields, initial, onSubmit, onCancel, submitting, autofill }) {
  const [form, setForm] = useState(() => ({ ...initial }));
  const [errors, setErrors] = useState({});

  // Optional auto-calculate: when the trigger fields change (e.g. Payroll's
  // employee/month/year), fetch a computed draft and fill the target fields.
  const firstRun = useRef(true);
  const triggerKey = autofill ? autofill.trigger.map((k) => form[k]).join("|") : "";
  useEffect(() => {
    if (!autofill) return;
    const primary = autofill.trigger[0];
    if (!form[primary]) return;                       // need at least the primary (e.g. employee)
    if (firstRun.current && initial?.id) { firstRun.current = false; return; } // don't clobber an existing record on open
    firstRun.current = false;
    const params = {};
    autofill.trigger.forEach((k) => { if (form[k]) params[k] = form[k]; });
    api.get(`/${autofill.endpoint}/`, { params })
      .then(({ data }) => setForm((f) => {
        const next = { ...f };
        autofill.fills.forEach((k) => { if (data[k] !== undefined && data[k] !== null) next[k] = data[k]; });
        return next;
      }))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [triggerKey]);
  const set = (k, v) => {
    setForm((f) => {
      const next = { ...f, [k]: v };
      // changing a parent field resets any field that depends on it
      fields.forEach((fld) => { if (fld.dependsOn === k) next[fld.key] = ""; });
      return next;
    });
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
              <RefSelect
                field={f}
                value={form[f.key]}
                onChange={(v) => set(f.key, v)}
                filterParam={f.dependsOn && form[f.dependsOn] ? { [f.dependsParam || f.dependsOn]: form[f.dependsOn] } : undefined}
              />
            ) : f.type === "creatable" ? (
              <CreatableSelect field={f} value={form[f.key]} onChange={(v) => set(f.key, v)} />
            ) : f.type === "select" ? (
              <select className={inputCls(f)} value={form[f.key] ?? ""} onChange={(e) => set(f.key, e.target.value)}>
                <option value="">Select {f.label}</option>
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
