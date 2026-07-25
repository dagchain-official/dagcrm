import { Phone, Clock, Users, CheckCircle2, Gauge, Coins, Wallet, GraduationCap } from "lucide-react";

// The sales scorecard, styled like the dashboard's top KPI cards. Leads and
// Revenue are intentionally NOT here — they already appear in the cards above,
// so this shows only the extra KPIs. `data` is the endpoint's `kpis` block
// (already scoped by role: a Sales Executive sees only their own numbers).
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

const CARDS = [
  { key: "calls", label: "Calls", icon: Phone, color: "bg-sky-100 text-sky-600", fmt: num },
  { key: "talk_time", label: "Talk Time", icon: Clock, color: "bg-indigo-100 text-indigo-600", fmt: num },
  { key: "meetings", label: "Meetings", icon: Users, color: "bg-violet-100 text-violet-600", fmt: num },
  { key: "sales", label: "Sales", icon: CheckCircle2, color: "bg-emerald-100 text-emerald-600", fmt: num },
  { key: "overall_kpi", label: "Overall KPI", icon: Gauge, color: "bg-amber-100 text-amber-600", fmt: num },
  { key: "incentive_earned", label: "Incentive Earned", icon: Coins, color: "bg-teal-100 text-teal-600", fmt: money },
  { key: "incentive_paid", label: "Incentive Paid", icon: Wallet, color: "bg-rose-100 text-rose-500", fmt: money },
  { key: "training", label: "Training", icon: GraduationCap, color: "bg-orange-100 text-orange-600", fmt: num },
];

export default function KpiScorecard({ data, title = "KPIs · This Month" }) {
  const k = data || {};
  return (
    <div className="space-y-3">
      <h3 className="font-bold text-ink-900">{title}</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {CARDS.map(({ key, label, icon: Icon, color, fmt }) => (
          <div key={key} className="card p-5">
            <div className={`grid place-items-center w-11 h-11 rounded-2xl ${color}`}>
              <Icon size={20} />
            </div>
            <p className="text-3xl font-extrabold text-ink-900 mt-4 tabular-nums">{fmt(k[key])}</p>
            <p className="text-sm text-ink-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
