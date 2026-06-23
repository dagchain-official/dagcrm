import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FileText, Plus, Trash2, Pencil, Send, FileDown, Search, Check, Ban, GitBranch } from "lucide-react";
import api from "../api/client";
import { Badge, Spinner, EmptyState, ConfirmModal } from "../components/ui";
import ProposalBuilder, { blankProposal, blankItem } from "../components/ProposalBuilder";
import { STATUS_COLORS } from "../config/resources";
import { useToast } from "../context/ToastContext";

const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
const date = (v) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—");

export default function Proposals() {
  const toast = useToast();
  const [rows, setRows] = useState(null);
  const [search, setSearch] = useState("");
  const [builder, setBuilder] = useState(null);
  const [confirmRow, setConfirmRow] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [params, setParams] = useSearchParams();

  const load = () => api.get("/proposals/", { params: { search: search || undefined, page_size: 100 } })
    .then(({ data }) => setRows(data.results || data)).catch(() => setRows([]));
  useEffect(() => { const t = setTimeout(load, search ? 300 : 0); return () => clearTimeout(t); }, [search]);

  // opened from a Lead/Customer profile "Send Proposal" → pre-fill the builder
  useEffect(() => {
    const lead = params.get("lead");
    const customer = params.get("customer");
    const name = params.get("name");
    if (lead || customer) {
      setBuilder({
        ...blankProposal(),
        contactType: customer ? "customer" : "lead",
        lead: lead || "", customer: customer || "",
        title: name ? `Proposal for ${name}` : "",
      });
      setParams({}, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const edit = async (row) => {
    const { data } = await api.get(`/proposals/${row.id}/`);
    setBuilder({
      id: data.id, title: data.title, contactType: data.customer ? "customer" : "lead",
      lead: data.lead || "", customer: data.customer || "", business: data.business || "",
      valid_until: data.valid_until || "", notes: data.notes || "", tax_percent: data.tax_percent || 0,
      items: data.items.length ? data.items : [blankItem()],
    });
  };
  const send = async (row) => { await api.post(`/proposals/${row.id}/send/`); toast.success("Proposal sent"); load(); };
  const revise = async (row) => {
    const { data } = await api.post(`/proposals/${row.id}/revise/`);
    toast.success(`Revision v${data.version} created (draft)`);
    edit(data);
    load();
  };
  const accept = async (row) => {
    await api.post(`/proposals/${row.id}/accept/`);
    toast.success("Accepted → opportunity won, revenue booked & customer updated");
    load();
  };
  const reject = async (row) => { await api.post(`/proposals/${row.id}/reject/`); toast.info("Proposal marked rejected"); load(); };
  const pdf = async (row) => {
    const { data, headers } = await api.get(`/proposals/${row.id}/pdf/`, { responseType: "blob" });
    const url = URL.createObjectURL(new Blob([data], { type: headers["content-type"] }));
    const a = document.createElement("a"); a.href = url; a.download = `proposal-${row.id}.pdf`; a.click(); URL.revokeObjectURL(url);
  };
  const del = async () => {
    setDeleting(true);
    try { await api.delete(`/proposals/${confirmRow.id}/`); toast.success("Deleted"); setConfirmRow(null); load(); }
    finally { setDeleting(false); }
  };

  if (!rows) return <Spinner label="Loading proposals…" />;
  const sent = rows.filter((r) => r.status === "sent" || r.status === "accepted").length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900 flex items-center gap-2"><FileText className="text-brand-600" /> Proposals</h1>
          <p className="text-sm text-ink-400">{rows.length} total · {sent} sent</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="chip !py-2">
            <Search size={16} className="text-ink-400" />
            <input className="text-sm outline-none bg-transparent w-40 text-ink-700" placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <button className="btn-primary" onClick={() => setBuilder(blankProposal())}><Plus size={16} /> New Proposal</button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[["Total", rows.length, "text-ink-900"], ["Sent", sent, "text-emerald-600"],
          ["Draft", rows.filter((r) => r.status === "draft").length, "text-amber-600"]].map(([l, v, c]) => (
          <div key={l} className="card p-5"><p className={`text-3xl font-extrabold tabular-nums ${c}`}>{v}</p><p className="text-sm text-ink-400 mt-0.5">{l}</p></div>
        ))}
      </div>

      <div className="card p-5">
        {rows.length === 0 ? <EmptyState title="No proposals yet" hint="Click “New Proposal” to build one." /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                  <th className="pb-3 px-3 font-semibold">Ref #</th>
                  <th className="pb-3 px-3 font-semibold">Title</th>
                  <th className="pb-3 px-3 font-semibold">For</th>
                  <th className="pb-3 px-3 font-semibold">Items</th>
                  <th className="pb-3 px-3 font-semibold text-right">Total</th>
                  <th className="pb-3 px-3 font-semibold">Status</th>
                  <th className="pb-3 px-3 font-semibold">Sent</th>
                  <th className="pb-3 px-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className={`border-t border-ink-100 hover:bg-ink-50/70 ${r.is_current ? "" : "opacity-60"}`}>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-ink-700">{r.number || "—"}</span>
                      <span className="ml-1.5 text-[10px] font-bold text-brand-600">v{r.version}</span>
                      {r.revision_count > 1 && <span className="ml-1 text-[10px] text-ink-400">/{r.revision_count}</span>}
                    </td>
                    <td className="py-3 px-3 font-medium text-ink-800">{r.title}</td>
                    <td className="py-3 px-3 text-ink-500">{r.contact}</td>
                    <td className="py-3 px-3 text-ink-500">{r.item_count}</td>
                    <td className="py-3 px-3 text-right font-semibold text-ink-900 tabular-nums">{money(r.total)}</td>
                    <td className="py-3 px-3"><Badge value={r.status} map={STATUS_COLORS} /></td>
                    <td className="py-3 px-3 text-ink-500">{r.sent_at ? date(r.sent_at) : "—"}</td>
                    <td className="py-3 px-3">
                      <div className="flex justify-end gap-1">
                        {r.status === "draft" && <button className="btn text-xs px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100" onClick={() => send(r)}><Send size={13} /> Send</button>}
                        {r.status === "sent" && <>
                          <button className="btn text-xs px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100" title="Mark accepted" onClick={() => accept(r)}><Check size={13} /> Accept</button>
                          <button className="btn text-xs px-2 py-1 bg-rose-50 text-rose-600 hover:bg-rose-100" title="Mark rejected" onClick={() => reject(r)}><Ban size={13} /></button>
                        </>}
                        <button className="btn-ghost p-1.5 text-brand-600" title="Download PDF" onClick={() => pdf(r)}><FileDown size={15} /></button>
                        {r.status === "draft"
                          ? <button className="btn-ghost p-1.5" title="Edit draft" onClick={() => edit(r)}><Pencil size={15} /></button>
                          : <button className="btn-ghost p-1.5 text-violet-600" title="Create new version" onClick={() => revise(r)}><GitBranch size={15} /></button>}
                        {r.status !== "accepted" && <button className="btn-ghost p-1.5 text-rose-500 hover:bg-rose-50" title="Delete" onClick={() => setConfirmRow(r)}><Trash2 size={15} /></button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {builder && <ProposalBuilder initial={builder} onClose={() => setBuilder(null)} onSaved={() => { setBuilder(null); load(); }} />}
      <ConfirmModal open={!!confirmRow} busy={deleting} onClose={() => setConfirmRow(null)} onConfirm={del}
        title="Delete Proposal?" message="Ye proposal permanently delete ho jayega." />
    </div>
  );
}
