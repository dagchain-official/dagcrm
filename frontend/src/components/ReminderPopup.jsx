import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Bell, X, Calendar, Clock, PhoneCall } from "lucide-react";
import api from "../api/client";

const DAY_KEY = "dagos_reminder_day";       // last date the daily popup was shown
const ALERT_KEY = "dagos_reminder_alerted"; // item keys already alerted (timed)

const todayStr = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD, local
const loadAlerted = () => {
  try { return new Set(JSON.parse(localStorage.getItem(ALERT_KEY) || "[]")); } catch { return new Set(); }
};
const saveAlerted = (set) => localStorage.setItem(ALERT_KEY, JSON.stringify([...set].slice(-80)));
const mkey = (prefix, m) => `${prefix}:${m.lead_id}-${m.at}`;

// Popups: (1) once per day on first open — meetings + callbacks + overdue follow-ups;
// (2) ~30 min before each meeting, ~2 min before each callback/follow-up (or if
// it's already due) — a focused alert for just that item.
export default function ReminderPopup() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const [imminent, setImminent] = useState(null); // {..., type} for a focused alert, else null
  const dataRef = useRef(null);

  const check = () => {
    const d = dataRef.current;
    if (!d || open) return;
    const now = Date.now();
    const set = loadAlerted();
    for (const m of d.meetings || []) {              // meetings: 30 min before
      const mins = (new Date(m.at).getTime() - now) / 60000;
      if (mins > 0 && mins <= 30 && !set.has(mkey("m", m))) {
        set.add(mkey("m", m)); saveAlerted(set);
        setImminent({ ...m, type: "meeting" }); setOpen(true); return;
      }
    }
    for (const c of d.callbacks || []) {             // callback / follow-up: 2 min before or overdue
      const mins = (new Date(c.at).getTime() - now) / 60000;
      if (mins <= 2 && !set.has(mkey("c", c))) {
        set.add(mkey("c", c)); saveAlerted(set);
        setImminent({ ...c, type: c.kind || "callback" }); setOpen(true); return;
      }
    }
  };

  useEffect(() => {
    let ticks = 0;
    const fetchAndMaybeOpen = (showDaily) => api.get("/leads/reminders/").then((r) => {
      dataRef.current = r.data; setData(r.data);
      const n = (r.data.meetings?.length || 0) + (r.data.overdue_followups?.length || 0) + (r.data.callbacks?.length || 0);
      if (showDaily && n > 0 && localStorage.getItem(DAY_KEY) !== todayStr()) {
        localStorage.setItem(DAY_KEY, todayStr());
        setImminent(null); setOpen(true);
      } else {
        check();
      }
    }).catch(() => {});

    fetchAndMaybeOpen(true);
    const t = setInterval(() => {
      ticks += 1;
      if (ticks % 5 === 0) fetchAndMaybeOpen(false); // refresh list every 5 min
      else check();                                  // check timed alerts every min
    }, 60000);
    return () => clearInterval(t);
  }, []);

  if (!open || !data) return null;
  const dt = (v) => new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const close = () => { setOpen(false); setImminent(null); };

  const meetings = imminent ? (imminent.type === "meeting" ? [imminent] : []) : (data.meetings || []);
  const callbacks = imminent ? (imminent.type !== "meeting" ? [imminent] : []) : (data.callbacks || []);
  const overdue = imminent ? [] : (data.overdue_followups || []);

  let heading = "Reminders";
  if (imminent) {
    const mins = Math.round((new Date(imminent.at).getTime() - Date.now()) / 60000);
    const noun = imminent.type === "meeting" ? "Meeting" : imminent.type === "followup" ? "Follow-up" : "Callback";
    heading = mins > 0 ? `${noun} in ~${mins} min` : `${noun} due now`;
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={close}>
      <div className="card p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-ink-900 flex items-center gap-2">
            <Bell size={18} className="text-brand-600" /> {heading}
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
          {callbacks.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-400 uppercase tracking-wide mb-1.5">
                {imminent ? "Call now" : "Callbacks & follow-ups"}
              </p>
              {callbacks.map((c, i) => (
                <Link key={i} to={`/leads/${c.lead_id}`} onClick={close}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 mb-1.5 hover:bg-emerald-500/20">
                  <PhoneCall size={15} className="text-emerald-600 shrink-0" />
                  <span className="text-sm text-ink-700"><b className="text-ink-900">{c.lead}</b> · {c.kind === "followup" ? "follow up" : "call back"} {dt(c.at)}</span>
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
