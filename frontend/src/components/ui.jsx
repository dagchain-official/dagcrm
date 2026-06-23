import { X, AlertTriangle } from "lucide-react";

export function Badge({ value, map }) {
  const cls = map?.[value] || "bg-ink-100 text-ink-600";
  return <span className={`badge ${cls}`}>{String(value ?? "").replace("_", " ")}</span>;
}

export function ScorePill({ value }) {
  const v = Number(value) || 0;
  const color = v >= 75 ? "bg-emerald-500" : v >= 50 ? "bg-amber-500" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 rounded-full bg-ink-200 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${v}%` }} />
      </div>
      <span className="text-xs font-semibold text-ink-600 tabular-nums">{v}</span>
    </div>
  );
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-400">
      <span className="w-5 h-5 border-2 border-ink-300 border-t-brand-600 rounded-full animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function TableSkeleton({ rows = 8, cols = 5 }) {
  return (
    <div className="overflow-hidden">
      <div className="flex gap-4 pb-3 border-b border-ink-100">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="skeleton h-3 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-4 border-b border-ink-100 last:border-0">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton h-3.5 flex-1" style={{ opacity: 1 - r * 0.05 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", hint }) {
  return (
    <div className="text-center py-16">
      <p className="text-ink-600 font-semibold">{title}</p>
      {hint && <p className="text-sm text-ink-400 mt-1">{hint}</p>}
    </div>
  );
}

export function Modal({ open, onClose, title, children, footer }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="card w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-200">
          <h3 className="font-bold text-ink-900">{title}</h3>
          <button onClick={onClose} className="text-ink-400 hover:text-ink-700">
            <X size={20} />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto">{children}</div>
        {footer && <div className="px-6 py-4 border-t border-ink-200 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

export function ConfirmModal({
  open, onClose, onConfirm, busy,
  title = "Are you sure?", message = "This action cannot be undone.",
  confirmLabel = "Delete",
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="card w-full max-w-sm p-6">
        <div className="grid place-items-center w-14 h-14 rounded-2xl bg-rose-50 text-rose-500 mx-auto">
          <AlertTriangle size={26} />
        </div>
        <h3 className="text-lg font-extrabold text-ink-900 text-center mt-4">{title}</h3>
        <p className="text-sm text-ink-500 text-center mt-1.5">{message}</p>
        <div className="flex gap-2 mt-6">
          <button className="btn-ghost flex-1 border border-ink-200" onClick={onClose} disabled={busy}>Cancel</button>
          <button className="btn flex-1 bg-rose-600 text-white hover:bg-rose-700" onClick={onConfirm} disabled={busy}>
            {busy ? "Deleting…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
