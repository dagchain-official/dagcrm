import { useEffect, useState } from "react";
import {
  LogIn, LogOut, Clock, Phone, StickyNote, Ticket as TicketIcon,
  Activity, Coffee, Timer,
} from "lucide-react";
import api from "../api/client";
import { Spinner } from "../components/ui";

const fmtTime = (d) => d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const fmtDate = (d) => d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
const clock = (v) => (v ? new Date(v).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) : "—");
const mins = (m) => {
  const h = Math.floor((m || 0) / 60), x = (m || 0) % 60;
  return h ? `${h}h ${x}m` : `${x}m`;
};

function Stat({ icon: Icon, label, value, tint }) {
  return (
    <div className="card p-4 flex items-center gap-3">
      <div className={`grid place-items-center w-10 h-10 rounded-xl ${tint}`}><Icon size={18} /></div>
      <div>
        <p className="text-lg font-extrabold text-ink-900 tabular-nums leading-tight">{value}</p>
        <p className="text-xs text-ink-400">{label}</p>
      </div>
    </div>
  );
}

export default function MyAttendance() {
  const [now, setNow] = useState(new Date());
  const [att, setAtt] = useState(null);
  const [act, setAct] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const load = () => {
    api.get("/attendance/today/").then((r) => setAtt(r.data)).catch(() => {});
    api.get("/activity/today/").then((r) => setAct(r.data)).catch(() => {});
  };
  useEffect(() => {
    load();
    const t = setInterval(() => api.get("/activity/today/").then((r) => setAct(r.data)).catch(() => {}), 60000);
    return () => clearInterval(t);
  }, []);

  const action = async (path) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/attendance/${path}/`);
      setAtt(data);
    } finally {
      setBusy(false);
    }
  };

  if (!att) return <Spinner label="Loading attendance…" />;

  const total = (act?.active_duration || 0) + (act?.idle_duration || 0) || 1;
  const activePct = Math.round(((act?.active_duration || 0) / total) * 100);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-ink-900">My Attendance</h1>
        <p className="text-sm text-ink-400">Real-time check-in & activity tracking</p>
      </div>

      {/* clock + check in/out */}
      <div className="card p-8 bg-gradient-to-br from-brand-600 to-brand-500 text-white border-0 relative overflow-hidden">
        <div className="absolute -top-12 -right-10 w-56 h-56 rounded-full bg-white/10" />
        <div className="relative flex flex-col lg:flex-row lg:items-center gap-8">
          <div className="flex-1">
            <p className="text-white/70 text-sm">{fmtDate(now)}</p>
            <p className="text-5xl lg:text-6xl font-extrabold tabular-nums tracking-tight mt-1">{fmtTime(now)}</p>
            <div className="flex flex-wrap gap-x-6 gap-y-1 mt-4 text-sm text-white/80">
              <span>Check-in: <b className="text-white">{clock(att.checkin)}</b></span>
              <span>Check-out: <b className="text-white">{clock(att.checkout)}</b></span>
              <span>Worked: <b className="text-white">{att.working_hours}h</b></span>
            </div>
          </div>
          <div className="shrink-0">
            {!att.checked_in ? (
              <button onClick={() => action("check-in")} disabled={busy}
                className="btn bg-white text-brand-700 hover:bg-white/90 text-base px-6 py-3 shadow-lg">
                <LogIn size={18} /> Check In
              </button>
            ) : !att.checked_out ? (
              <button onClick={() => action("check-out")} disabled={busy}
                className="btn bg-white text-rose-600 hover:bg-white/90 text-base px-6 py-3 shadow-lg">
                <LogOut size={18} /> Check Out
              </button>
            ) : (
              <div className="text-center px-6 py-3 rounded-xl bg-white/15">
                <p className="font-bold">✓ Day Complete</p>
                <p className="text-xs text-white/70">{att.working_hours}h worked</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* activity tracking */}
      {act && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <Stat icon={Timer} label="Total Logged" value={mins(act.login_duration)} tint="bg-brand-100 text-brand-600" />
            <Stat icon={Activity} label="Active Time" value={mins(act.active_duration)} tint="bg-emerald-100 text-emerald-600" />
            <Stat icon={Coffee} label="Idle Time" value={mins(act.idle_duration)} tint="bg-amber-100 text-amber-600" />
          </div>

          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-ink-900">Activity Ratio</h3>
              <span className="text-sm font-semibold text-emerald-600">{activePct}% active</span>
            </div>
            <div className="h-3 rounded-full bg-ink-100 overflow-hidden flex">
              <div className="bg-emerald-500 h-full" style={{ width: `${activePct}%` }} />
              <div className="bg-amber-400 h-full" style={{ width: `${100 - activePct}%` }} />
            </div>
            <p className="text-xs text-ink-400 mt-2">Auto-tracked from your activity (updates every minute).</p>
          </div>

          <div>
            <h3 className="font-bold text-ink-900 mb-3">Today's Work (auto-counted)</h3>
            <div className="grid grid-cols-3 gap-4">
              <Stat icon={Phone} label="Calls Logged" value={act.calls_completed} tint="bg-blue-100 text-blue-600" />
              <Stat icon={StickyNote} label="Notes Added" value={act.notes_added} tint="bg-violet-100 text-violet-600" />
              <Stat icon={TicketIcon} label="Tickets Updated" value={act.tickets_updated} tint="bg-rose-100 text-rose-500" />
            </div>
            <p className="text-xs text-ink-400 mt-2">
              Logging a <b>Call</b> or <b>Note</b> activity, or updating a ticket, increments these automatically.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
