import { useEffect, useState } from "react";
import api from "../api/client";

// Loads options from a DRF endpoint and renders a <select>.
// `filterParam` (e.g. { business: 3 }) scopes the options (dependent dropdown).
export default function RefSelect({ field, value, onChange, placeholder, filterParam }) {
  const [opts, setOpts] = useState([]);
  const key = JSON.stringify(filterParam || {});

  useEffect(() => {
    api
      .get(`/${field.ref}/`, { params: { page_size: 200, ...(filterParam || {}) } })
      .then(({ data }) => setOpts(data.results || data))
      .catch(() => setOpts([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field.ref, key]);

  return (
    <select className="input" value={value ?? ""} onChange={(e) => onChange(e.target.value || null)}>
      <option value="">{placeholder || `Select ${field.label || "option"}`}</option>
      {opts.map((o) => (
        <option key={o.id} value={o.id}>
          {o[field.labelKey] || o.label || o.name || o.title || `#${o.id}`}
        </option>
      ))}
    </select>
  );
}
