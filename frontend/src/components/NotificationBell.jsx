import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";
import api from "../api/client";

const KIND_DOT = {
  success: "bg-emerald-500", warning: "bg-amber-500", error: "bg-rose-500", info: "bg-brand-500",
};
const ago = (v) => {
  const s = Math.floor((Date.now() - new Date(v)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

export default function NotificationBell() {
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const box = useRef(null);
  const nav = useNavigate();

  const loadCount = () => api.get("/notifications/unread_count/").then(({ data }) => setCount(data.count)).catch(() => {});
  const loadItems = () => api.get("/notifications/").then(({ data }) => setItems(data.results || data)).catch(() => {});

  useEffect(() => {
    loadCount();
    const t = setInterval(() => { if (!document.hidden) loadCount(); }, 30000);
    const onClick = (e) => box.current && !box.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", onClick);
    return () => { clearInterval(t); document.removeEventListener("mousedown", onClick); };
  }, []);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) loadItems();
  };

  const markAll = async () => {
    await api.post("/notifications/mark_all_read/");
    setCount(0);
    loadItems();
  };

  const click = async (n) => {
    if (!n.is_read) { await api.post(`/notifications/${n.id}/read/`); loadCount(); }
    if (n.link) { setOpen(false); nav(n.link); }
  };

  return (
    <div ref={box} className="relative">
      <button onClick={toggle} className="btn-ghost p-2 relative">
        <Bell size={19} />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 grid place-items-center text-[10px] font-bold text-white bg-rose-500 rounded-full">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute top-full right-0 mt-2 w-80 card p-0 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-ink-200">
            <p className="font-bold text-ink-900 text-sm">Notifications</p>
            {items.some((i) => !i.is_read) && (
              <button onClick={markAll} className="text-xs font-semibold text-brand-600 flex items-center gap-1">
                <CheckCheck size={13} /> Mark all read
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {items.length === 0 ? (
              <p className="text-sm text-ink-400 px-4 py-8 text-center">You're all caught up 🎉</p>
            ) : (
              items.map((n) => (
                <button key={n.id} onClick={() => click(n)}
                  className={`w-full text-left px-4 py-3 border-b border-ink-100 last:border-0 hover:bg-ink-50 flex gap-3 ${n.is_read ? "" : "bg-brand-50/40"}`}>
                  <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${KIND_DOT[n.kind] || KIND_DOT.info}`} />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink-800">{n.title}</p>
                    {n.body && <p className="text-xs text-ink-500">{n.body}</p>}
                    <p className="text-[11px] text-ink-400 mt-0.5">{ago(n.created_at)}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
