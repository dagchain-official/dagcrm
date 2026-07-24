import { useEffect, useState } from "react";
import { Coins, ChevronDown, ChevronRight, Check, Info, Plus, X } from "lucide-react";
import api from "../api/client";
import { Spinner, EmptyState } from "../components/ui";
import { useToast } from "../context/ToastContext";

// Set a commission rate per product, with an optional per-RM override.
//   FX Artha · Lots  -> a $ amount per lot
//   DAGChain products -> a % of the node price; Staking -> a % of the DGC staked
export default function CommissionRules() {
  const toast = useToast();
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [platform, setPlatform] = useState("fxartha");
  const [open, setOpen] = useState({});          // product key -> overrides expanded
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [newRate, setNewRate] = useState("");

  const load = () => api.get("/reports/commission-rules/")
    .then((r) => { setD(r.data); setErr(""); })
    .catch(() => setErr("You don't have access to commission rules."));
  useEffect(() => { load(); }, []);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading commission rules…" />;

  const products = d.products[platform] || [];
  const employees = d.employees || [];
  const overrides = d.overrides[platform] || {};      // {emp_id: {key: rate}}
  const canEdit = d.can_edit;
  // a $ amount for a per-lot base, otherwise a percent
  const isAmount = (p) => p.basis === "amount";
  const suffix = (p) => (isAmount(p) ? "$" : "%");

  const save = (product_key, rate, employee) => {
    if (!canEdit) return;
    api.put("/reports/commission-rules/", { platform, product_key, rate, employee })
      .then(() => { toast.success("Saved"); load(); })
      .catch(() => toast.error("Could not save"));
  };

  const addProduct = () => {
    const name = newName.trim();
    if (!name) return;
    api.put("/reports/commission-rules/", { platform, product_key: name, rate: newRate || 0 })
      .then(() => {
        toast.success("Product added");
        setAdding(false); setNewName(""); setNewRate(""); load();
      })
      .catch(() => toast.error("Could not add"));
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2">
          <Coins className="text-brand-600" /> Commission Rules
        </h1>
        <p className="text-sm text-ink-400">A rate per product, with an optional per-RM override. Applies to every existing record the moment you save — no backfill.</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 p-1 bg-ink-100 rounded-xl w-fit">
          {[["fxartha", "FX Artha"], ["dagchain", "DAGChain"]].map(([k, l]) => (
            <button key={k} onClick={() => { setPlatform(k); setAdding(false); }}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${platform === k ? "bg-ink-0 text-brand-700 shadow-sm" : "text-ink-500 hover:text-ink-700"}`}>
              {l}
            </button>
          ))}
        </div>
        {canEdit && !adding && (
          <button onClick={() => setAdding(true)} className="btn-primary !py-2 !px-4 text-sm inline-flex items-center gap-1.5">
            <Plus size={15} /> Add product
          </button>
        )}
      </div>

      {adding && (
        <div className="card p-4 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="label">
              {platform === "dagchain" ? "Node package / tier name" : "Product / base name"}
            </label>
            <input className="input" value={newName} autoFocus placeholder={platform === "dagchain" ? "e.g. Standard Tier" : "e.g. Insurance"}
              onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addProduct()} />
          </div>
          <div>
            <label className="label">Rate {platform === "fxartha" ? "($)" : "(%)"}</label>
            <input className="input !w-28" type="number" step="0.01" min="0" value={newRate}
              onChange={(e) => setNewRate(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addProduct()} />
          </div>
          <button onClick={addProduct} className="btn-primary !py-2.5 !px-4 text-sm">Add</button>
          <button onClick={() => { setAdding(false); setNewName(""); setNewRate(""); }} className="chip !py-2.5 text-sm inline-flex items-center gap-1"><X size={14} /> Cancel</button>
          <p className="text-xs text-ink-400 basis-full">
            {platform === "dagchain"
              ? "Matches nodes by this exact package name — use it to pre-set a rate for a tier that isn't sold yet."
              : "A custom base only pays once its data is wired; the built-in Lots, Brokerage and Deposit already compute."}
          </p>
        </div>
      )}

      {!canEdit && (
        <div className="card p-3 flex items-center gap-2 text-sm text-ink-500">
          <Info size={15} /> View only — ask an administrator to change rates.
        </div>
      )}

      {products.length === 0 && (
        <EmptyState title="No products yet" hint={platform === "dagchain" ? "DAGChain node packages appear here once nodes are synced." : "The FX Artha per-lot rate appears here."} />
      )}

      <div className="space-y-3">
        {products.map((p) => {
          const isOpen = open[p.key];
          const overriddenCount = employees.filter((e) => overrides[e.id]?.[p.key] != null).length;
          return (
            <div key={p.key} className="card overflow-hidden">
              <div className="flex flex-wrap items-center gap-3 p-4">
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-ink-900 truncate">{p.label}{p.custom && <span className="ml-1.5 badge bg-ink-100 text-ink-500">custom</span>}</p>
                  <p className="text-xs text-ink-400">{p.kind && p.kind !== "custom" ? `${p.kind} · ` : ""}{p.unit}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-ink-400">Universal</span>
                  <RateInput value={p.rate} disabled={!canEdit} suffix={suffix(p)}
                    onSave={(v) => save(p.key, v, null)} />
                </div>
                <button onClick={() => setOpen((o) => ({ ...o, [p.key]: !o[p.key] }))}
                  className="chip !py-1.5 text-xs inline-flex items-center gap-1">
                  {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  Per-RM{overriddenCount ? ` (${overriddenCount})` : ""}
                </button>
              </div>
              {isOpen && (
                <div className="border-t border-ink-100 divide-y divide-ink-50">
                  {employees.length === 0 && <p className="p-4 text-sm text-ink-400">No RMs to override.</p>}
                  {employees.map((e) => (
                    <div key={e.id} className="flex items-center gap-3 px-4 py-2.5">
                      <span className="flex-1 text-sm text-ink-700">{e.name}</span>
                      <RateInput value={overrides[e.id]?.[p.key]} disabled={!canEdit}
                        placeholder={`${p.rate}`} suffix={suffix(p)}
                        onSave={(v) => save(p.key, v, e.id)} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RateInput({ value, onSave, disabled, suffix, placeholder }) {
  const [v, setV] = useState(value ?? "");
  const [saved, setSaved] = useState(false);
  useEffect(() => { setV(value ?? ""); }, [value]);
  const commit = () => {
    if (String(v) === String(value ?? "")) return;
    onSave(v);
    setSaved(true); setTimeout(() => setSaved(false), 1500);
  };
  return (
    <div className="flex items-center gap-1 chip !py-1.5">
      <input className="w-16 bg-transparent outline-none text-sm tabular-nums text-right" type="number"
        step="0.01" min="0" disabled={disabled} value={v} placeholder={placeholder}
        onChange={(e) => setV(e.target.value)} onBlur={commit}
        onKeyDown={(e) => e.key === "Enter" && e.target.blur()} />
      <span className="text-ink-400 text-xs w-3">{saved ? <Check size={12} className="text-emerald-600" /> : suffix}</span>
    </div>
  );
}
