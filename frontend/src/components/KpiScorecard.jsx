// The sales-department scorecard — the same 10 fields on every role's dashboard.
// `data` is the `kpis` block from the dashboard endpoint (already scoped by role).
const money = (v) => `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const num = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

export default function KpiScorecard({ data, title = "KPIs · This Month" }) {
  const k = data || {};
  const fields = [
    ["Leads", num(k.leads)], ["Calls", num(k.calls)], ["Talk Time", num(k.talk_time)],
    ["Meetings", num(k.meetings)], ["Sales", num(k.sales)],
    ["Revenue", money(k.revenue)], ["Overall KPI", num(k.overall_kpi)],
    ["Incentive Earned", money(k.incentive_earned)], ["Incentive Paid", money(k.incentive_paid)],
    ["Training", num(k.training)],
  ];
  return (
    <div className="card p-5">
      <h3 className="font-bold text-ink-900 mb-4">{title}</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-ink-50 border border-ink-100 px-4 py-3 text-center">
            <p className="text-xs font-semibold text-ink-500">{label}</p>
            <p className="text-xl font-extrabold text-ink-900 tabular-nums mt-1">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
