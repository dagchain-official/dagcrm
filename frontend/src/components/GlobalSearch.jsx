import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UserPlus, UserCheck, LifeBuoy } from "lucide-react";
import api from "../api/client";

const ICON = { Lead: UserPlus, Customer: UserCheck, Ticket: LifeBuoy };

export default function GlobalSearch() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const box = useRef(null);
  const nav = useNavigate();

  useEffect(() => {
    const onClick = (e) => box.current && !box.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  useEffect(() => {
    if (q.trim().length < 2) { setResults([]); return; }
    const t = setTimeout(() => {
      api.get("/search/", { params: { q } }).then(({ data }) => { setResults(data.results); setOpen(true); }).catch(() => {});
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const go = (r) => { setOpen(false); setQ(""); nav(r.link); };

  return (
    <div ref={box} className="relative hidden md:block flex-1 max-w-md">
      <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-ink-100 text-ink-400">
        <Search size={16} />
        <input
          className="text-sm bg-transparent outline-none w-full text-ink-700 placeholder-ink-400"
          placeholder="Search leads, customers, tickets…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
        />
      </div>
      {open && (
        <div className="absolute top-full mt-2 w-full card p-2 z-50 max-h-80 overflow-y-auto">
          {results.length === 0 ? (
            <p className="text-sm text-ink-400 px-3 py-4 text-center">No matches</p>
          ) : (
            results.map((r) => {
              const Icon = ICON[r.type] || Search;
              return (
                <button key={`${r.type}-${r.id}`} onClick={() => go(r)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-ink-50 text-left">
                  <div className="grid place-items-center w-8 h-8 rounded-lg bg-brand-50 text-brand-600 shrink-0"><Icon size={15} /></div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink-800 truncate">{r.title}</p>
                    <p className="text-xs text-ink-400 truncate">{r.type} · {r.subtitle}</p>
                  </div>
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
