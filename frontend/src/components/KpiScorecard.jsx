import { Link } from "react-router-dom";
import { Phone, PhoneCall, Clock, Timer, Target, Repeat, Users, CalendarClock,
  CalendarCheck2, CheckCircle2, Gauge, Coins, Wallet, GraduationCap,
  ShieldCheck, CalendarCheck, UserCheck } from "lucide-react";

// The sales scorecard, styled like the dashboard's top KPI cards. Leads and
// Revenue are intentionally NOT here — they already appear in the cards above,
// so this shows only the extra KPIs. `data` is the endpoint's `kpis` block
// (already scoped by role: a Sales Executive sees only their own numbers).
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
const pct = (v) => `${(Number(v || 0) * 100).toFixed(0)}%`;

// `to` = which section a card opens on click.
const ACT = "/m/lead-activities";   // calls / talk / callbacks / meetings live here
const CARDS = [
  { key: "calls", label: "Calls", icon: Phone, color: "bg-sky-100 text-sky-600", fmt: num, to: ACT },
  { key: "contact_rate", label: "Contact Rate", icon: Target, color: "bg-blue-100 text-blue-600", fmt: pct, to: ACT },
  { key: "connect_rate", label: "Connect Rate", icon: PhoneCall, color: "bg-sky-100 text-sky-600", fmt: pct, to: ACT },
  { key: "talk_time", label: "Talk Time (min)", icon: Clock, color: "bg-indigo-100 text-indigo-600", fmt: num, to: ACT },
  { key: "avg_talk_min", label: "Avg Talk (min)", icon: Timer, color: "bg-indigo-100 text-indigo-600", fmt: num, to: ACT },
  { key: "callbacks_due", label: "Callbacks Due", icon: Repeat, color: "bg-amber-100 text-amber-600", fmt: num, to: ACT },
  { key: "callbacks_completed", label: "Callbacks Done", icon: Repeat, color: "bg-emerald-100 text-emerald-600", fmt: num, to: ACT },
  { key: "meetings_booked", label: "Meetings Booked", icon: CalendarClock, color: "bg-violet-100 text-violet-600", fmt: num, to: ACT },
  { key: "meetings_done", label: "Meetings Done", icon: CalendarCheck2, color: "bg-violet-100 text-violet-600", fmt: num, to: ACT },
  { key: "sales", label: "Sales", icon: CheckCircle2, color: "bg-emerald-100 text-emerald-600", fmt: num, to: "/m/opportunities" },
  { key: "quality_score", label: "Quality Score", icon: ShieldCheck, color: "bg-fuchsia-100 text-fuchsia-600", fmt: pct, to: "/kpi" },
  { key: "followup_compliance", label: "Follow-up Compliance", icon: CalendarCheck, color: "bg-cyan-100 text-cyan-600", fmt: pct, to: ACT },
  { key: "attendance", label: "Attendance", icon: UserCheck, color: "bg-lime-100 text-lime-600", fmt: pct, to: "/attendance-clock" },
  { key: "overall_kpi", label: "Overall KPI", icon: Gauge, color: "bg-amber-100 text-amber-600", fmt: num, to: "/kpi" },
  { key: "incentive_earned", label: "Incentive Earned", icon: Coins, color: "bg-teal-100 text-teal-600", fmt: money, to: "/kpi" },
  { key: "incentive_paid", label: "Incentive Paid", icon: Wallet, color: "bg-rose-100 text-rose-500", fmt: money, to: "/kpi" },
  { key: "training", label: "Training", icon: GraduationCap, color: "bg-orange-100 text-orange-600", fmt: pct, to: "/kpi" },
];

export default function KpiScorecard({ data, title = "KPIs · This Month" }) {
  const k = data || {};
  return (
    <div className="space-y-3">
      <h3 className="font-bold text-ink-900">{title}</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {CARDS.map(({ key, label, icon: Icon, color, fmt, to }) => (
          <Link key={key} to={to} className="card p-5 hover:shadow-md hover:-translate-y-0.5 transition block">
            <div className={`grid place-items-center w-11 h-11 rounded-2xl ${color}`}>
              <Icon size={20} />
            </div>
            <p className="text-3xl font-extrabold text-ink-900 mt-4 tabular-nums">{fmt(k[key])}</p>
            <p className="text-sm text-ink-400 mt-0.5">{label}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
