import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Plus, Pencil, Trash2, Search, Eye, Download, Check, X, Upload, FileSpreadsheet, Calculator, FileDown, Shuffle, ChevronLeft, ChevronRight } from "lucide-react";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import api from "../api/client";
import { RESOURCES, STATUS_COLORS } from "../config/resources";
import { Badge, ConfirmModal, EmptyState, Modal, ScorePill, TableSkeleton } from "../components/ui";
import DataForm from "../components/DataForm";
import RefSelect from "../components/RefSelect";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

const PAGE_SIZE = 25;

const money = (v) => (v == null || v === "" ? "—" : `$${Number(v).toLocaleString()}`);
const dt = (v) => (v ? new Date(v).toLocaleString() : "—");

function Progress({ value }) {
  const v = Math.round(Number(value) || 0);
  const color = v >= 100 ? "bg-emerald-500" : v >= 50 ? "bg-brand-500" : "bg-amber-500";
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 rounded-full bg-ink-200 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${Math.min(100, v)}%` }} />
      </div>
      <span className="text-xs font-semibold text-ink-600 tabular-nums w-9 text-right">{v}%</span>
    </div>
  );
}

function exportPdf(name, columns, rows) {
  const doc = new jsPDF({ orientation: columns.length > 5 ? "landscape" : "portrait" });
  doc.setFontSize(16);
  doc.setTextColor("#4f46e5");
  doc.text(`DAGOS — ${name}`, 14, 16);
  doc.setFontSize(9);
  doc.setTextColor("#94a3b8");
  doc.text(new Date().toLocaleString(), 14, 22);
  autoTable(doc, {
    startY: 26,
    head: [columns.map((c) => c.label)],
    body: rows.map((r) => columns.map((c) => (r[c.key] == null ? "" : String(r[c.key])))),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [79, 70, 229] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  });
  doc.save(`${name}.pdf`);
}

function exportCsv(name, columns, rows) {
  const headers = columns.map((c) => c.label);
  const lines = rows.map((r) =>
    columns.map((c) => {
      let v = r[c.key];
      if (v == null) v = "";
      v = String(v).replace(/"/g, '""');
      return `"${v}"`;
    }).join(",")
  );
  const csv = [headers.join(","), ...lines].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${name}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResourceTable({ resource: propResource }) {
  const params = useParams();
  const resource = propResource || params.resource;
  const cfg = RESOURCES[resource];
  const { can, user } = useAuth();
  const toast = useToast();
  const canCreate = can(resource, "create");
  const canEdit = can(resource, "edit");
  const canDelete = can(resource, "delete");
  // `adminOnly` columns (e.g. Lead phone) are visible only to super admin / business head
  const columns = cfg.columns.filter((c) => !c.adminOnly || user?.is_admin_view);

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [modal, setModal] = useState(null);
  const [saving, setSaving] = useState(false);
  const [confirmRow, setConfirmRow] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);
  const now = new Date();
  const [recalcOpen, setRecalcOpen] = useState(false);
  const [recalc, setRecalc] = useState({ month: now.getMonth() + 1, year: now.getFullYear() });
  const [recalcResult, setRecalcResult] = useState(null);
  const [recalcing, setRecalcing] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [distOpen, setDistOpen] = useState(false);
  const [dist, setDist] = useState({ strategy: "round_robin", user_id: "" });
  const [distResult, setDistResult] = useState(null);
  const [distRunning, setDistRunning] = useState(false);
  const [users, setUsers] = useState([]);

  const load = useCallback((silent = false) => {
    if (!cfg) return;
    if (!silent) setLoading(true);
    const params = { search: search || undefined, page, page_size: PAGE_SIZE, ...filters };
    Object.keys(params).forEach((k) => (params[k] === "" || params[k] == null) && delete params[k]);
    api
      .get(`/${cfg.endpoint}/`, { params })
      .then(({ data }) => {
        setRows(data.results || data);
        setCount(data.count ?? (data.results || data).length);
      })
      .catch(() => { if (!silent) { setRows([]); setCount(0); } })
      .finally(() => { if (!silent) setLoading(false); });
  }, [cfg, search, filters, page]);

  useEffect(() => {
    setSearch("");
    setFilters({});
    setPage(1);
  }, [resource]);
  useEffect(() => {
    const t = setTimeout(load, search ? 350 : 0);
    return () => clearTimeout(t);
  }, [load, search]);

  // live auto-refresh — list updates without manual reload
  useEffect(() => {
    const id = setInterval(() => { if (!document.hidden) load(true); }, 1000);
    return () => clearInterval(id);
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  const blank = useMemo(
    () => Object.fromEntries((cfg?.fields || []).map((f) => [f.key, ""])),
    [cfg]
  );

  if (!cfg) return <EmptyState title="Unknown module" hint={resource} />;

  const fetchAll = async () => {
    const params = { search: search || undefined, page_size: 5000, ...filters };
    Object.keys(params).forEach((k) => (params[k] === "" || params[k] == null) && delete params[k]);
    const { data } = await api.get(`/${cfg.endpoint}/`, { params });
    return data.results || data;
  };
  const doExport = async (fmt) => {
    try {
      const all = await fetchAll();
      (fmt === "pdf" ? exportPdf : exportCsv)(cfg.title, columns, all);
      toast.success(`Exported ${all.length} ${cfg.title.toLowerCase()} as ${fmt.toUpperCase()}`);
    } catch {
      toast.error("Export failed");
    }
  };

  const save = async (form) => {
    setSaving(true);
    const payload = { ...form };
    Object.keys(payload).forEach((k) => payload[k] === "" && delete payload[k]);
    try {
      if (modal.mode === "edit") await api.patch(`/${cfg.endpoint}/${modal.row.id}/`, payload);
      else await api.post(`/${cfg.endpoint}/`, payload);
      setModal(null);
      load();
      toast.success(`${cfg.title} ${modal.mode === "edit" ? "updated" : "created"}`);
    } catch (e) {
      const d = e.response?.data;
      toast.error("Save failed: " + (typeof d === "object" ? Object.values(d).flat()[0] : d || e.message));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    const row = confirmRow;
    setDeleting(true);
    try {
      await api.delete(`/${cfg.endpoint}/${row.id}/`);
      if (rows.length === 1 && page > 1) setPage(page - 1);
      else load();
      toast.success("Deleted");
      setConfirmRow(null);
    } catch {
      toast.error("Delete failed");
    } finally {
      setDeleting(false);
    }
  };

  const doImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post(`/${cfg.endpoint}/import_csv/`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportResult(data);
      load();
    } catch (e2) {
      setImportResult({ error: e2.response?.data?.detail || "Import failed" });
    } finally {
      setImporting(false);
      e.target.value = "";
    }
  };

  const runRecalc = async () => {
    setRecalcing(true);
    setRecalcResult(null);
    try {
      const { data } = await api.post(`/${cfg.recalc.path}/`, recalc);
      setRecalcResult(data);
      load();
    } catch (e2) {
      setRecalcResult({ error: e2.response?.data?.detail || "Calculation failed" });
    } finally {
      setRecalcing(false);
    }
  };

  const runAction = async (act, row) => {
    try {
      if (act.download) {
        const { data, headers } = await api.get(`/${act.download(row.id)}`, { responseType: "blob" });
        const url = URL.createObjectURL(new Blob([data], { type: headers["content-type"] }));
        const a = document.createElement("a");
        a.href = url;
        a.download = `${act.label}-${row.id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      await api.post(`/${act.post(row.id)}`);
      load();
      toast.success(`${act.label} done`);
    } catch (e) {
      toast.error("Action failed: " + (e.response?.data?.detail || e.message));
    }
  };

  const openDistribute = () => {
    setDistResult(null);
    setDistOpen(true);
    if (!users.length) api.get("/users/assignable/").then(({ data }) => setUsers(data.results || data)).catch(() => {});
  };
  const runDistribute = async () => {
    setDistRunning(true);
    setDistResult(null);
    try {
      const body = { strategy: dist.strategy };
      if (dist.strategy === "manual") body.user_id = Number(dist.user_id);
      const { data } = await api.post(`/${cfg.distribute.path}/`, body);
      setDistResult(data);
      load();
    } catch (e) {
      setDistResult({ error: e.response?.data?.detail || "Distribution failed" });
    } finally {
      setDistRunning(false);
    }
  };

  const cell = (col, row) => {
    const v = row[col.key];
    if (col.badge) return <Badge value={v} map={STATUS_COLORS} />;
    if (col.score) return <ScorePill value={v} />;
    if (col.progress) return <Progress value={v} />;
    if (col.money) return <span className="tabular-nums">{money(v)}</span>;
    if (col.datetime) return dt(v);
    return v ?? "—";
  };

  const actMatches = (act, row) =>
    !act.when || Object.entries(act.when).every(([k, val]) => row[k] === val);
  const hasRowActions = (cfg.rowActions || []).length > 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-ink-900">{cfg.title}</h1>
          <p className="text-sm text-ink-400">{count} record{count !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {(cfg.filters || []).map((f) => (
            f.ref ? (
              <div key={f.key} className="w-44">
                <RefSelect field={f} placeholder={`All ${f.label}s`} value={filters[f.key] ?? ""} onChange={(v) => { setPage(1); setFilters((s) => ({ ...s, [f.key]: v })); }} />
              </div>
            ) : (
              <select key={f.key} className="input !py-2 w-auto" value={filters[f.key] ?? ""}
                onChange={(e) => { setPage(1); setFilters((s) => ({ ...s, [f.key]: e.target.value })); }}>
                <option value="">All {f.label}</option>
                {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            )
          ))}
          {cfg.search && (
            <div className="chip !py-2" data-tour="rt-search">
              <Search size={16} className="text-ink-400" />
              <input className="text-sm outline-none bg-transparent w-36 text-ink-700"
                placeholder="Search…" value={search} onChange={(e) => { setPage(1); setSearch(e.target.value); }} />
            </div>
          )}
          {rows.length > 0 && (
            <div className="relative" data-tour="rt-export">
              <button className="chip !py-2" onClick={() => setExportOpen((o) => !o)} onBlur={() => setTimeout(() => setExportOpen(false), 150)} title="Export">
                <Download size={15} /> Export
              </button>
              {exportOpen && (
                <div className="absolute right-0 top-full mt-1 card p-1 z-30 w-32">
                  <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-ink-50 text-sm flex items-center gap-2"
                    onMouseDown={() => doExport("csv")}><FileSpreadsheet size={14} /> CSV</button>
                  <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-ink-50 text-sm flex items-center gap-2"
                    onMouseDown={() => doExport("pdf")}><FileDown size={14} /> PDF</button>
                </div>
              )}
            </div>
          )}
          {cfg.distribute && canEdit && user?.can_assign_leads && (
            <button className="chip !py-2" onClick={openDistribute} title="Auto-assign leads to RMs">
              <Shuffle size={15} /> Distribute
            </button>
          )}
          {cfg.importable && canCreate && (
            <button className="chip !py-2" onClick={() => { setImportResult(null); setImportOpen(true); }} title="Import from CSV">
              <Upload size={15} /> Import
            </button>
          )}
          {cfg.recalc && canCreate && (
            <button className="chip !py-2" onClick={() => { setRecalcResult(null); setRecalcOpen(true); }} title="Auto-calculate from revenue">
              <Calculator size={15} /> Auto-Calculate
            </button>
          )}
          {canCreate && (resource !== "leads" || user?.can_assign_leads) && (
            <button className="btn-primary" data-tour="rt-new" onClick={() => setModal({ mode: "create", row: blank })}>
              <Plus size={16} /> New
            </button>
          )}
        </div>
      </div>

      <div className="card p-5">
        {loading ? (
          <TableSkeleton cols={Math.min(columns.length + 1, 6)} />
        ) : rows.length === 0 ? (
          <EmptyState title="No records" hint="Try adjusting filters or click “New”." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-400 text-xs uppercase tracking-wide">
                  <th className="pb-3 pr-4 font-semibold">S/N</th>
                  {columns.map((c) => (
                    <th key={c.key} className="pb-3 px-4 font-semibold whitespace-nowrap">{c.label}</th>
                  ))}
                  <th className="pb-3 px-4 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={row.id} className="border-t border-ink-100 hover:bg-ink-50/70 transition">
                    <td className="py-3.5 pr-4 text-ink-400 tabular-nums">{String(i + 1).padStart(2, "0")}</td>
                    {columns.map((c) => (
                      <td key={c.key} className="py-3.5 px-4 text-ink-700 whitespace-nowrap max-w-[220px] truncate">
                        {cell(c, row)}
                      </td>
                    ))}
                    <td className="py-3.5 px-4">
                      <div className="flex justify-end items-center gap-1">
                        {hasRowActions && cfg.rowActions.filter((a) => actMatches(a, row)).map((a) => {
                          const tint = a.variant === "success" ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                            : a.variant === "info" ? "bg-brand-50 text-brand-700 hover:bg-brand-100"
                            : "bg-rose-50 text-rose-600 hover:bg-rose-100";
                          const Icon = a.icon === "check" ? Check : a.icon === "download" ? FileDown : X;
                          return (
                            <button key={a.label} onClick={() => runAction(a, row)} className={`btn text-xs px-2.5 py-1 ${tint}`}>
                              <Icon size={13} /> {a.label}
                            </button>
                          );
                        })}
                        {cfg.detailPath && (
                          <Link to={`${cfg.detailPath}/${row.id}`} className="btn-ghost p-1.5 text-brand-600" title="Open 360 view">
                            <Eye size={15} />
                          </Link>
                        )}
                        {canEdit && (
                          <button className="btn-ghost p-1.5" onClick={() => setModal({ mode: "edit", row })}>
                            <Pencil size={15} />
                          </button>
                        )}
                        {canDelete && (
                          <button className="btn-ghost p-1.5 text-rose-500 hover:bg-rose-50" onClick={() => setConfirmRow(row)}>
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && count > PAGE_SIZE && (
          <div className="flex items-center justify-between gap-3 pt-4 mt-2 border-t border-ink-100">
            <p className="text-xs text-ink-400">
              Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, count)} of {count}
            </p>
            <div className="flex items-center gap-1">
              <button className="btn-ghost px-2.5 py-1.5 disabled:opacity-40" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm font-semibold text-ink-700 px-2">{page} / {totalPages}</span>
              <button className="btn-ghost px-2.5 py-1.5 disabled:opacity-40" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      <Modal open={!!modal} onClose={() => setModal(null)}
        title={`${modal?.mode === "edit" ? "Edit" : "New"} ${cfg.title}`}>
        {modal && (
          <DataForm fields={cfg.fields} initial={modal.row} submitting={saving} autofill={cfg.autofill}
            onSubmit={save} onCancel={() => setModal(null)} />
        )}
      </Modal>

      <ConfirmModal
        open={!!confirmRow}
        busy={deleting}
        onClose={() => setConfirmRow(null)}
        onConfirm={remove}
        title={`Delete ${cfg.title.replace(/s$/, "")}?`}
        message="This record will be permanently deleted. Are you sure?"
      />

      <Modal open={importOpen} onClose={() => setImportOpen(false)} title={`Import ${cfg.title} from CSV`}>
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-ink-50 border border-ink-100 text-sm text-ink-600">
            <p className="font-semibold text-ink-800 mb-1">CSV format</p>
            <p>Columns: <code className="text-brand-600">name, email, phone, country, source, status</code>.
              Duplicates (same email/phone) are skipped automatically.</p>
            <a href={`${api.defaults.baseURL}/${cfg.endpoint}/import_template/`} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-1.5 mt-2 text-brand-600 font-semibold">
              <FileSpreadsheet size={15} /> Download template
            </a>
          </div>

          <label className="flex flex-col items-center justify-center gap-2 p-8 rounded-2xl border-2 border-dashed border-ink-200 hover:border-brand-400 cursor-pointer transition">
            <Upload size={26} className="text-ink-400" />
            <span className="text-sm font-semibold text-ink-700">{importing ? "Importing…" : "Click to choose a CSV file"}</span>
            <input type="file" accept=".csv" className="hidden" onChange={doImport} disabled={importing} />
          </label>

          {importResult && (
            importResult.error ? (
              <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{importResult.error}</div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-3 rounded-xl bg-emerald-50"><p className="text-xl font-extrabold text-emerald-600">{importResult.created}</p><p className="text-xs text-ink-500">Created</p></div>
                  <div className="p-3 rounded-xl bg-amber-50"><p className="text-xl font-extrabold text-amber-600">{importResult.skipped}</p><p className="text-xs text-ink-500">Skipped</p></div>
                  <div className="p-3 rounded-xl bg-rose-50"><p className="text-xl font-extrabold text-rose-500">{importResult.total_errors}</p><p className="text-xs text-ink-500">Errors</p></div>
                </div>
                {importResult.errors?.length > 0 && (
                  <div className="max-h-32 overflow-y-auto text-xs text-ink-500 space-y-0.5">
                    {importResult.errors.map((er, i) => <p key={i}>Row {er.row}: {er.reason}</p>)}
                  </div>
                )}
              </div>
            )
          )}
        </div>
      </Modal>

      {cfg.recalc && (
        <Modal open={recalcOpen} onClose={() => setRecalcOpen(false)} title={cfg.recalc.title}
          footer={
            <>
              <button className="btn-ghost" onClick={() => setRecalcOpen(false)}>Close</button>
              <button className="btn-primary" onClick={runRecalc} disabled={recalcing}>
                {recalcing ? "Calculating…" : "Run"}
              </button>
            </>
          }>
          <div className="space-y-4">
            <p className="text-sm text-ink-500">
              Incentives are computed from each RM's revenue using their business's incentive rule,
              then pushed into that month's payroll.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Month</label>
                <select className="input" value={recalc.month} onChange={(e) => setRecalc({ ...recalc, month: +e.target.value })}>
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Year</label>
                <input className="input" type="number" value={recalc.year} onChange={(e) => setRecalc({ ...recalc, year: +e.target.value })} />
              </div>
            </div>
            {recalcResult && (
              recalcResult.error ? (
                <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{recalcResult.error}</div>
              ) : (
                <div className="space-y-2">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-3 rounded-xl bg-emerald-50"><p className="text-xl font-extrabold text-emerald-600">{recalcResult.employees_credited}</p><p className="text-xs text-ink-500">Employees</p></div>
                    <div className="p-3 rounded-xl bg-brand-50"><p className="text-lg font-extrabold text-brand-600">${Number(recalcResult.total_amount).toLocaleString()}</p><p className="text-xs text-ink-500">Total</p></div>
                    <div className="p-3 rounded-xl bg-violet-50"><p className="text-xl font-extrabold text-violet-600">{recalcResult.payrolls_updated}</p><p className="text-xs text-ink-500">Payrolls</p></div>
                  </div>
                  <p className="text-xs text-ink-400">
                    {recalcResult.incentives_created} created · {recalcResult.incentives_updated} updated ·
                    skipped {recalcResult.skipped_no_owner} (no RM) / {recalcResult.skipped_no_rule} (no rule)
                  </p>
                </div>
              )
            )}
          </div>
        </Modal>
      )}

      {cfg.distribute && (
        <Modal open={distOpen} onClose={() => setDistOpen(false)} title="Distribute Leads to RMs"
          footer={
            <>
              <button className="btn-ghost" onClick={() => setDistOpen(false)}>Close</button>
              <button className="btn-primary" onClick={runDistribute} disabled={distRunning || (dist.strategy === "manual" && !dist.user_id)}>
                {distRunning ? "Assigning…" : "Distribute"}
              </button>
            </>
          }>
          <div className="space-y-4">
            <p className="text-sm text-ink-500">Unassigned leads will be auto-assigned to RMs (Sales Executive / Team Leader).</p>
            <div>
              <label className="label">Strategy</label>
              <div className="space-y-2">
                {[
                  ["round_robin", "Round Robin", "Evenly balanced — fewest-load RM gets the next lead"],
                  ["performance", "Performance Based", "Top performers (higher conversion) get more leads"],
                  ["manual", "Manual", "Assign all to one specific RM"],
                ].map(([val, label, desc]) => (
                  <label key={val} className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer ${dist.strategy === val ? "border-brand-300 bg-brand-50" : "border-ink-200"}`}>
                    <input type="radio" name="strategy" className="mt-1" checked={dist.strategy === val} onChange={() => setDist({ ...dist, strategy: val })} />
                    <div><p className="text-sm font-semibold text-ink-800">{label}</p><p className="text-xs text-ink-400">{desc}</p></div>
                  </label>
                ))}
              </div>
            </div>
            {dist.strategy === "manual" && (
              <div>
                <label className="label">Assign to</label>
                <select className="input" value={dist.user_id} onChange={(e) => setDist({ ...dist, user_id: e.target.value })}>
                  <option value="">— select RM —</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.name} — {u.role_name}</option>)}
                </select>
              </div>
            )}
            {distResult && (
              distResult.error ? (
                <div className="px-3 py-2 rounded-xl bg-rose-50 text-rose-600 text-sm">{distResult.error}</div>
              ) : !distResult.assigned ? (
                <div className="px-3 py-2 rounded-xl bg-amber-50 text-amber-700 text-sm">
                  {distResult.detail || "No unassigned leads to distribute."}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-emerald-50 text-sm">
                  <p className="font-semibold text-emerald-700">
                    ✓ {distResult.assigned} lead{distResult.assigned !== 1 ? "s" : ""} assigned
                    {distResult.strategy ? ` (${distResult.strategy.replace(/_/g, " ")})` : ""}
                  </p>
                  {distResult.breakdown && (
                    <div className="mt-1 text-xs text-ink-600">
                      {Object.entries(distResult.breakdown).map(([n, c]) => <span key={n} className="inline-block mr-3">{n}: {c}</span>)}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
