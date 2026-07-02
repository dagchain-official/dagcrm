import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import api from "../api/client";

// A <select> whose options are the distinct existing values of a field
// (e.g. every Metric "name" already in the DB), plus an inline "➕ Add new…"
// that lets the user type a new value. The new value shows in the dropdown
// immediately and is persisted to the DB when the parent record is saved.
export default function CreatableSelect({ field, value, onChange }) {
  const { endpoint, field: valueField } = field.optionsFrom || {};
  const [opts, setOpts] = useState([]);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (!endpoint) return;
    api.get(`/${endpoint}/`, { params: { page_size: 500 } })
      .then(({ data }) => {
        const rows = data.results || data;
        const vals = [...new Set(rows.map((r) => r[valueField]).filter(Boolean))].sort();
        setOpts(vals);
      })
      .catch(() => setOpts([]));
  }, [endpoint, valueField]);

  // keep the current value visible even if it isn't in the fetched list yet
  const options = value && !opts.includes(value) ? [value, ...opts] : opts;

  const confirmAdd = () => {
    const v = draft.trim();
    if (!v) return;
    if (!opts.includes(v)) setOpts((o) => [...o, v].sort());
    onChange(v);
    setDraft("");
    setAdding(false);
  };

  if (adding) {
    return (
      <div className="flex gap-1.5">
        <input
          autoFocus
          className="input flex-1"
          value={draft}
          placeholder="Type new value…"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); confirmAdd(); }
            if (e.key === "Escape") { setAdding(false); setDraft(""); }
          }}
        />
        <button type="button" className="btn-primary !px-3" onClick={confirmAdd}><Check size={15} /></button>
        <button type="button" className="btn-ghost border border-ink-200 !px-3" onClick={() => { setAdding(false); setDraft(""); }}><X size={15} /></button>
      </div>
    );
  }

  return (
    <select
      className="input"
      value={value ?? ""}
      onChange={(e) => (e.target.value === "__add__" ? setAdding(true) : onChange(e.target.value))}
    >
      <option value="">Select {field.label}</option>
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
      <option value="__add__">➕ Add new…</option>
    </select>
  );
}
