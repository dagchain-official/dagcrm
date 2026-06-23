import { useEffect, useState } from "react";
import { Plus, Send, X } from "lucide-react";
import api from "../api/client";
import { Modal } from "./ui";
import RefSelect from "./RefSelect";
import { useToast } from "../context/ToastContext";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
const lineNet = (it) => (Number(it.quantity) || 0) * (Number(it.unit_price) || 0) * (1 - (Number(it.discount) || 0) / 100);
export const blankItem = () => ({ description: "", quantity: 1, unit_price: 0, discount: 0 });
export const blankProposal = () => ({
  title: "", contactType: "lead", lead: "", customer: "", business: "",
  valid_until: "", notes: "", tax_percent: 0, items: [blankItem()],
});

// Reusable proposal builder modal. Open it from anywhere (Proposals page,
// Lead detail, Customer 360) with a pre-filled `initial`.
export default function ProposalBuilder({ initial, onClose, onSaved }) {
  const toast = useToast();
  const [f, setF] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [products, setProducts] = useState([]);
  const set = (k, v) => setF((s) => ({ ...s, [k]: v }));
  const setItem = (i, k, v) => setF((s) => ({ ...s, items: s.items.map((it, j) => (j === i ? { ...it, [k]: v } : it)) }));
  const addItem = () => setF((s) => ({ ...s, items: [...s.items, blankItem()] }));
  const delItem = (i) => setF((s) => ({ ...s, items: s.items.filter((_, j) => j !== i) }));

  useEffect(() => {
    if (!f.business) { setProducts([]); return; }
    api.get("/products/", { params: { business: f.business, page_size: 200 } })
      .then(({ data }) => setProducts(data.results || data)).catch(() => setProducts([]));
  }, [f.business]);

  useEffect(() => {
    if (f.contactType !== "lead" || !f.lead) return;
    api.get("/lead-interests/", { params: { lead: f.lead } })
      .then(({ data }) => {
        const r = data.results || data;
        if (r.length && r[0].business && !f.business) set("business", r[0].business);
      }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f.lead, f.contactType]);

  const subtotal = f.items.reduce((s, it) => s + (Number(it.quantity) || 0) * (Number(it.unit_price) || 0), 0);
  const taxable = f.items.reduce((s, it) => s + lineNet(it), 0);
  const discountTotal = subtotal - taxable;
  const taxAmount = taxable * (Number(f.tax_percent) || 0) / 100;
  const total = taxable + taxAmount;

  const save = async (alsoSend) => {
    if (!f.title.trim()) return toast.error("Title required");
    if (f.contactType === "lead" && !f.lead) return toast.error("Select a lead");
    if (f.contactType === "customer" && !f.customer) return toast.error("Select a customer");
    setSaving(true);
    try {
      const payload = {
        title: f.title,
        lead: f.contactType === "lead" ? f.lead : null,
        customer: f.contactType === "customer" ? f.customer : null,
        business: f.business || null,
        valid_until: f.valid_until || null,
        notes: f.notes,
        tax_percent: Number(f.tax_percent) || 0,
        items: f.items.filter((it) => it.description.trim()).map((it) => ({
          description: it.description, quantity: Number(it.quantity) || 0,
          unit_price: Number(it.unit_price) || 0, discount: Number(it.discount) || 0,
        })),
      };
      const { data } = f.id
        ? await api.patch(`/proposals/${f.id}/`, payload)
        : await api.post("/proposals/", payload);
      if (alsoSend) { await api.post(`/proposals/${data.id}/send/`); toast.success("Proposal sent"); }
      else toast.success(f.id ? "Proposal updated" : "Proposal saved (draft)");
      onSaved?.(data);
    } catch (e) {
      toast.error("Save failed: " + JSON.stringify(e.response?.data || e.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open onClose={onClose} size="3xl" title={f.id ? "Edit Proposal" : "New Proposal"}
      footer={
        <>
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-ghost border border-ink-200" disabled={saving} onClick={() => save(false)}>Save Draft</button>
          <button className="btn-primary" disabled={saving} onClick={() => save(true)}><Send size={15} /> Save &amp; Send</button>
        </>
      }>
      <div className="space-y-5">
        {/* ---- Header: who / what / which business ---- */}
        <div className="rounded-xl border border-ink-100 bg-ink-50/50 p-4 space-y-4">
          <div>
            <label className="label">Proposal Title <span className="text-rose-500">*</span></label>
            <input className="input" value={f.title} onChange={(e) => set("title", e.target.value)} placeholder="e.g. Forex Managed Account Plan" />
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <label className="label">For</label>
              <select className="input" value={f.contactType} onChange={(e) => set("contactType", e.target.value)}>
                <option value="lead">Lead</option>
                <option value="customer">Customer</option>
              </select>
            </div>
            <div>
              <label className="label">{f.contactType === "lead" ? "Select Lead" : "Select Customer"}</label>
              {f.contactType === "lead"
                ? <RefSelect field={{ ref: "leads", labelKey: "name", label: "Lead" }} value={f.lead} onChange={(v) => set("lead", v)} />
                : <RefSelect field={{ ref: "customers", labelKey: "name", label: "Customer" }} value={f.customer} onChange={(v) => set("customer", v)} />}
            </div>
            <div>
              <label className="label">Business</label>
              <RefSelect field={{ ref: "businesses", labelKey: "name", label: "Business" }} value={f.business}
                onChange={(v) => { set("business", v); setF((s) => ({ ...s, items: s.items.map((it) => ({ ...it, description: "" })) })); }} />
            </div>
          </div>
          {f.contactType === "lead" && f.lead && f.business && <p className="text-xs text-emerald-600 -mt-1">Lead ke interest se business auto-detect hua</p>}
        </div>

        <div className="rounded-xl border border-ink-100 p-4">
          <div className="flex items-center justify-between mb-3">
            <label className="label !mb-0">Services / Items</label>
            <button className="text-xs font-semibold text-brand-600 flex items-center gap-1" onClick={addItem}><Plus size={13} /> Add item</button>
          </div>
          <div className="space-y-2">
            <div className="flex gap-2.5 text-[11px] text-ink-400 font-semibold uppercase px-1">
              <span className="flex-1">Service / Product</span>
              <span className="w-20 text-center">Qty</span>
              <span className="w-28 text-right">Unit Price</span>
              <span className="w-20 text-right">Disc %</span>
              <span className="w-28 text-right">Amount</span>
              <span className="w-6" />
            </div>
            {f.items.map((it, i) => (
              <div key={i} className="flex gap-2.5 items-center">
                {f.business ? (
                  <select className="input flex-1" value={it.description} onChange={(e) => setItem(i, "description", e.target.value)}>
                    <option value="">Select product / service</option>
                    {products.map((p) => <option key={p.id} value={p.name}>{p.name}</option>)}
                  </select>
                ) : (
                  <input className="input flex-1 !bg-ink-100 cursor-not-allowed" placeholder="Pehle business select karo" disabled />
                )}
                <input className="input w-20 text-center" type="number" value={it.quantity} onChange={(e) => setItem(i, "quantity", e.target.value)} />
                <input className="input w-28 text-right" type="number" value={it.unit_price} onChange={(e) => setItem(i, "unit_price", e.target.value)} />
                <input className="input w-20 text-right" type="number" min="0" max="100" value={it.discount} onChange={(e) => setItem(i, "discount", e.target.value)} />
                <span className="w-28 text-right text-sm font-semibold text-ink-700 tabular-nums">{money(lineNet(it))}</span>
                <button className="w-6 text-ink-300 hover:text-rose-500" onClick={() => delItem(i)} disabled={f.items.length === 1}><X size={15} /></button>
              </div>
            ))}
          </div>
          <div className="flex justify-end mt-4 pt-3 border-t border-ink-100">
            <div className="w-64 space-y-1.5 text-sm">
              <div className="flex justify-between text-ink-500"><span>Subtotal</span><span className="tabular-nums">{money(subtotal)}</span></div>
              {discountTotal > 0 && <div className="flex justify-between text-rose-500"><span>Discount</span><span className="tabular-nums">−{money(discountTotal)}</span></div>}
              <div className="flex justify-between items-center text-ink-500">
                <span className="flex items-center gap-1">Tax
                  <input className="input !w-14 !py-0.5 text-right" type="number" min="0" value={f.tax_percent} onChange={(e) => set("tax_percent", e.target.value)} />%
                </span>
                <span className="tabular-nums">{money(taxAmount)}</span>
              </div>
              <div className="flex justify-between pt-1.5 border-t border-ink-100 text-ink-900 font-extrabold text-lg">
                <span>Total</span><span className="tabular-nums">{money(total)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Valid Until</label>
            <input className="input" type="date" value={f.valid_until} onChange={(e) => set("valid_until", e.target.value)} />
          </div>
          <div>
            <label className="label">Notes</label>
            <input className="input" value={f.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Optional" />
          </div>
        </div>
      </div>
    </Modal>
  );
}
