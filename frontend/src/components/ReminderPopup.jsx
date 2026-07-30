import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, X, Calendar, Clock } from "lucide-react";
import api from "../api/client";

// On app open, pop up the agent's upcoming meetings + overdue follow-ups.
export default function ReminderPopup() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.get("/leads/reminders/").then((r) => {
      const n = (r.data.meetings?.length || 0) + (r.data.overdue_followups?.length || 0);
      if (n > 0) { setData(r.data); setOpen(true); }
    }).catch(() => {});
  }, []);

  if (!open || !data) return null;
  const dt = (v) => new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={() => setOpen(false)}>
      <div className="card p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-ink-900 flex items-center gap-2"><Bell size={18} className="text-brand-600" /> Reminders</h3>
          <button onClick={() => setOpen(false)} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>
        <div className="space-y-3 max-h-[60vh] overflow-y-auto">
          {data.meetings?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-1.5">Upcoming meetings</p>
              {data.meetings.map((m, i) => (
                <Link key={i} to={`/leads/${m.lead_id}`} onClick={() => setOpen(false)}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-brand-500/10 mb-1.5 hover:bg-brand-500/20">
                  <Calendar size={15} className="text-brand-600 shrink-0" />
                  <span className="text-sm text-ink-700"><b className="text-ink-900">{m.lead}</b> · {dt(m.at)}{m.location ? ` · ${m.location}` : ""}</span>
                </Link>
              ))}
            </div>
          )}
          {data.overdue_followups?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-1.5">Overdue follow-ups</p>
              {data.overdue_followups.map((o, i) => (
                <Link key={i} to={`/leads/${o.lead_id}`} onClick={() => setOpen(false)}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-500/10 mb-1.5 hover:bg-amber-500/20">
                  <Clock size={15} className="text-amber-600 shrink-0" />
                  <span className="text-sm text-ink-700"><b className="text-ink-900">{o.lead}</b> · no follow-up in {o.days} days</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
