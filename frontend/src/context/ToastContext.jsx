import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from "lucide-react";

const ToastContext = createContext(null);
export const useToast = () => useContext(ToastContext);

const CFG = {
  success: { icon: CheckCircle2, bar: "bg-emerald-500", tint: "text-emerald-600" },
  error: { icon: XCircle, bar: "bg-rose-500", tint: "text-rose-600" },
  warning: { icon: AlertTriangle, bar: "bg-amber-500", tint: "text-amber-600" },
  info: { icon: Info, bar: "bg-brand-500", tint: "text-brand-600" },
};

let _id = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const remove = (id) => setToasts((t) => t.filter((x) => x.id !== id));

  const push = (message, type = "info", ttl = 3800) => {
    const id = ++_id;
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => remove(id), ttl);
  };

  const toast = {
    success: (m) => push(m, "success"),
    error: (m) => push(m, "error"),
    warning: (m) => push(m, "warning"),
    info: (m) => push(m, "info"),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2 w-[min(92vw,360px)]">
        {toasts.map((t) => {
          const c = CFG[t.type] || CFG.info;
          const Icon = c.icon;
          return (
            <div key={t.id} className="card p-0 overflow-hidden flex items-stretch shadow-soft animate-[slidein_.2s_ease]">
              <div className={`w-1.5 ${c.bar}`} />
              <div className="flex items-start gap-3 px-4 py-3 flex-1">
                <Icon size={18} className={`${c.tint} mt-0.5 shrink-0`} />
                <p className="text-sm text-ink-700 flex-1">{t.message}</p>
                <button onClick={() => remove(t.id)} className="text-ink-300 hover:text-ink-600"><X size={15} /></button>
              </div>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
