import { useEffect, useState } from "react";
import api from "../api/client";

// Loads options from a DRF endpoint and renders a <select>.
export default function RefSelect({ field, value, onChange }) {
  const [opts, setOpts] = useState([]);

  useEffect(() => {
    api
      .get(`/${field.ref}/`, { params: { page_size: 200 } })
      .then(({ data }) => setOpts(data.results || data))
      .catch(() => setOpts([]));
  }, [field.ref]);

  return (
    <select className="input" value={value ?? ""} onChange={(e) => onChange(e.target.value || null)}>
      <option value="">— select —</option>
      {opts.map((o) => (
        <option key={o.id} value={o.id}>
          {o[field.labelKey] || o.name || `#${o.id}`}
        </option>
      ))}
    </select>
  );
}
