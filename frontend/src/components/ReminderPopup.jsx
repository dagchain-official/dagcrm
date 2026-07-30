import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Bell, X, Calendar, Clock } from "lucide-react";
import api from "../api/client";

const DAY_KEY = "dagos_reminder_day";      // last date the daily popup was shown
const MEET_KEY = "dagos_reminder_meetings"; // meeting keys already alerted (30-min)

const todayStr = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD, local
const loadAlerted = () => {
  try { return new Set(JSON.parse(localStorage.getItem(MEET_KEY) || "[]")); } catch { return new Set(); }
};
const saveAlerted = (set) => localStorage.setItem(MEET_KEY, JSON.stringify([...set].slice(-50)));
const mkey = (m) => `${m.lead_id}-${m.at}`;

// Popups: (1) once per day on first open — that day's meetings + overdue follow-ups;
// (2) ~30 min before each meeting — a focused alert for just that meeting.
export default function ReminderPopup() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [imminent, setImminent] = useState(null); // meeting for the 30-min alert, else null (daily view)
  const dataRef = useRef(null);

  const checkImminent = () => {
    const d = dataRef.current;
    if (!d || open) return;
    const now = Date.now();
    const set = loadAlerted();
    for (const m of d.meetings || []) {
      const mins = (new Date(m.at).getTime() - now) / 60000;
      if (mins > 0 && mins <= 30 && !set.has(mkey(m))) {
        set.add(mkey(m)); saveAlerted(set);
        setImminent(m); setOpen(true);
        return;
      }
    }
  };

  useEffect(() => {
    let ticks = 0;
    const fetchAndMaybeOpen = (showDaily) => api.get("/leads/reminders/").then((r) => {
      dataRef.current = r.data; setData(r.data);
      const n = (r.data.meetings?.length || 0) + (r.data.overdue_followups?.length || 0);
      if (showDaily && n > 0 && localStorage.getItem(DAY_KEY) !== todayStr()) {
        localStorage.setItem(DAY_KEY, todayStr());
        setImminent(null); setOpen(true);
      } else {
        checkImminent();
      }
    }).catch(() => {});

    fetchAndMaybeOpen(true);
    const t = setInterval(() => {
      ticks += 1;
      if (ticks % 5 === 0) fetchAndMaybeOpen(false); // refresh list every 5 min
      else checkImminent();                          // check 30-min window every min
    }, 60000);
    return () => clearInterval(t);
  }, []);

  if (!open || !data) return null;
  const dt = (v) => new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const close = () => { setOpen(false); setImminent(null); };

  const meetings = imminent ? [imminent] : (data.meetings || []);
  const overdue = imminent ? [] : (data.overdue_followups || []);
  const minsLeft = imminent ? Math.max(1, Math.round((new Date(imminent.at).getTime() - Date.now()) / 60000)) : 0;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={close}>
      <div className="card p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-ink-900 flex items-center gap-2">
            <Bell size={18} className="text-brand-600" />
            {imminent ? `Meeting in ~${minsLeft} min` : "Reminders"}
          </h3>
          <button onClick={close} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>
        <div className="space-y-3 max-h-[60vh] overflow-y-auto">
          {meetings.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-1.5">
                {imminent ? "Starting soon" : "Upcoming meetings"}
              </p>
              {meetings.map((m, i) => (
                <Link key={i} to={`/leads/${m.lead_id}`} onClick={close}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-brand-500/10 mb-1.5 hover:bg-brand-500/20">
                  <Calendar size={15} className="text-brand-600 shrink-0" />
                  <span className="text-sm text-ink-700"><b className="text-ink-900">{m.lead}</b> · {dt(m.at)}{m.location ? ` · ${m.location}` : ""}</span>
                </Link>
              ))}
            </div>
          )}
          {overdue.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-1.5">Overdue follow-ups</p>
              {overdue.map((o, i) => (
                <Link key={i} to={`/leads/${o.lead_id}`} onClick={close}
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
