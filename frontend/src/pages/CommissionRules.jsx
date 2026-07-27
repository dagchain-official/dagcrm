import { useEffect, useState } from "react";
import { Coins, ChevronDown, ChevronRight, Check, Info, Plus, X, Trash2, BookOpen } from "lucide-react";
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
  const [newBasis, setNewBasis] = useState("percent");   // "percent" | "amount"

  const load = () => api.get("/reports/commission-rules/")
    .then((r) => { setD(r.data); setErr(""); })
    .catch(() => setErr("You don't have access to commission rules."));
  useEffect(() => { load(); }, []);

  if (err) return <EmptyState title="No access" hint={err} />;
  if (!d) return <Spinner label="Loading commission rules…" />;

  const products = d.products[platform] || [];
  const catalogue = platform === "fxartha" ? d.catalogue?.fxartha : null;
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

  // clears a product's rate (and every per-RM override). A custom product then
  // disappears from the list; a built-in one just drops back to "no rate".
  const clearProduct = (p) => {
    if (!canEdit) return;
    const msg = p.custom
      ? `Delete "${p.label}"? Its rate and all overrides will be removed.`
      : `Clear the rate for "${p.label}" (and all its per-RM overrides)?`;
    if (!window.confirm(msg)) return;
    const empIds = employees.filter((e) => overrides[e.id]?.[p.key] != null).map((e) => e.id);
    Promise.all([
      api.put("/reports/commission-rules/", { platform, product_key: p.key, rate: "", employee: null }),
      ...empIds.map((id) => api.put("/reports/commission-rules/",
        { platform, product_key: p.key, rate: "", employee: id })),
    ]).then(() => { toast.success(p.custom ? "Deleted" : "Cleared"); load(); })
      .catch(() => toast.error("Could not delete"));
  };

  const addProduct = () => {
    const name = newName.trim();
    if (!name) { toast.error("Enter a product name"); return; }
    api.put("/reports/commission-rules/", { platform, product_key: name, rate: newRate || 0, basis: newBasis })
      .then(() => {
        toast.success(`Product “${name}” added`);
        setAdding(false); setNewName(""); setNewRate(""); setNewBasis("percent"); load();
      })
      .catch(() => toast.error("Could not add product"));
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
          {/* $ or % — how the rate is applied */}
          <div>
            <label className="label">Rate type</label>
            <div className="flex items-center rounded-lg bg-ink-100 p-0.5 text-sm">
              {[["percent", "%"], ["amount", "$"]].map(([v, l]) => (
                <button key={v} onClick={() => setNewBasis(v)}
                  className={`px-3.5 py-1.5 rounded-md font-semibold ${newBasis === v ? "bg-white text-brand-700 shadow-sm" : "text-ink-500"}`}>
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Rate ({newBasis === "amount" ? "$" : "%"})</label>
            <input className="input !w-28" type="number" step="0.01" min="0" value={newRate}
              onChange={(e) => setNewRate(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addProduct()} />
          </div>
          <button onClick={addProduct} className="btn-primary !py-2.5 !px-4 text-sm">Add</button>
          <button onClick={() => { setAdding(false); setNewName(""); setNewRate(""); setNewBasis("percent"); }} className="chip !py-2.5 text-sm inline-flex items-center gap-1"><X size={14} /> Cancel</button>
          <p className="text-xs text-ink-400 basis-full">
            <b>%</b> = a percent of the base; <b>$</b> = a flat amount {platform === "dagchain" ? "per node." : "per lot."}
            {platform === "dagchain"
              ? " Matches nodes by this exact package name — set a rate for a tier before it's sold."
              : " A custom base only pays once its data is wired; built-in Lots, Brokerage and Deposit already compute."}
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
                {canEdit && (
                  <button onClick={() => clearProduct(p)} title={p.custom ? "Delete product" : "Clear rate"}
                    className="grid place-items-center w-8 h-8 rounded-lg text-ink-400 hover:text-rose-600 hover:bg-rose-50 transition">
                    <Trash2 size={15} />
                  </button>
                )}
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

      {catalogue && <FxCatalogue cat={catalogue} />}
    </div>
  );
}

// FX Artha's live product catalogue (from /products) — reference only, so the
// admin sees the real account types + the platform's own rates when setting RM
// commission. Our RM payout still computes on Lots / Brokerage / Deposit above.
function FxCatalogue({ cat }) {
  const [open, setOpen] = useState(false);
  const types = cat.account_types || [];
  const pct = (v) => (v == null ? "—" : `${(Number(v) * 100).toFixed(3).replace(/\.?0+$/, "")}%`);
  const money = (v) => (v == null ? "—" : `$${Number(v).toLocaleString()}`);
  const counts = [
    ["Instruments", (cat.instruments || []).length],
    ["Staking plans", (cat.staking_plans || []).length],
    ["Insurance", (cat.insurance || []).length],
    ["VIP tiers", (cat.vip || []).length],
  ].filter(([, n]) => n);

  if (!types.length && !counts.length) return null;
  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex items-center gap-2 p-4 text-left">
        <BookOpen size={16} className="text-brand-600" />
        <span className="font-bold text-ink-900">FX Artha product catalogue</span>
        <span className="badge bg-ink-100 text-ink-500">reference</span>
        <span className="ml-auto text-ink-400">{open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span>
      </button>
      {open && (
        <div className="border-t border-ink-100 p-4 space-y-4">
          <p className="text-xs text-ink-400 flex items-center gap-1.5">
            <Info size={13} /> FX Artha's own account types &amp; rates, pulled live. Your RM commission is set on Lots / Brokerage / Deposit above — this is here as a reference.
          </p>
          {types.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[560px]">
                <thead>
                  <tr className="text-left text-ink-400 text-[11px] uppercase tracking-wide bg-ink-50">
                    <th className="py-2.5 px-3">Account type</th>
                    <th className="py-2.5 px-3 text-right">Min deposit</th>
                    <th className="py-2.5 px-3 text-right">Leverage</th>
                    <th className="py-2.5 px-3 text-right">Commission</th>
                    <th className="py-2.5 px-3 text-right">Spread markup</th>
                    <th className="py-2.5 px-3">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {types.map((t, i) => (
                    <tr key={i} className={`border-t border-ink-100 ${t.is_active ? "" : "opacity-50"}`}>
                      <td className="py-2.5 px-3 font-semibold text-ink-800">{t.name}</td>
                      <td className="py-2.5 px-3 text-right tabular-nums">{money(t.minimum_deposit)}</td>
                      <td className="py-2.5 px-3 text-right tabular-nums">{t.leverage ? `1:${t.leverage}` : "—"}</td>
                      <td className="py-2.5 px-3 text-right tabular-nums">{t.commission_pct != null ? pct(t.commission_pct) : (t.commission ? money(t.commission) : "—")}</td>
                      <td className="py-2.5 px-3 text-right tabular-nums">{t.spread_markup ? pct(t.spread_markup) : "—"}</td>
                      <td className="py-2.5 px-3 text-xs text-ink-500">
                        {[t.swap_free && "swap-free", t.is_demo && "demo", !t.is_active && "inactive"].filter(Boolean).join(" · ") || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {counts.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {counts.map(([label, n]) => (
                <span key={label} className="chip !py-1.5 text-xs">{label}: <b className="ml-1 text-ink-800">{n}</b></span>
              ))}
            </div>
          )}
        </div>
      )}
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
