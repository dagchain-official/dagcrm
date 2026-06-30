"""Performance Model (PART 13) — 3 scorecards combined by admin weightage.

Each employee gets three 0-100 dimension scores, peer-normalised (the leader on
a signal scores 100), then combined with configurable weights
(PerformanceWeight, default 60 / 25 / 15):

  Revenue  = mean(revenue generated vs peers, target attainment %)
  Growth   = mean over growth-category KPIs (PART 6), each vs peers
  Activity = mean over activity-category KPIs (PART 6), each vs peers

Composes existing engines: revenue via the P&L attribution path, target
attainment from PART 5 (CTC × multiplier), growth/activity from PART 6 metrics.
Scores are per individual (own signals), not team-rolled.
"""
from decimal import Decimal

from apps.crm.models import MetricDefinition
from apps.hr.models import Employee, PerformanceWeight, TargetMultiplier

from .metrics import _leaf_stats
from .pnl import _revenue_by_user


def _norm(value, peak):
    return round(value / peak * 100, 1) if peak else 0.0


def compute_performance(month, year):
    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    if not emps:
        return {"month": month, "year": year, "rows": []}

    by_user, _ = _revenue_by_user(month, year)

    # target multiplier resolver (own CTC × multiplier → target)
    rows_mult = list(TargetMultiplier.objects.filter(status="active"))
    glob = next((r.multiplier for r in rows_mult if r.scope == "global"), None)
    by_level = {r.hierarchy_level_id: r.multiplier for r in rows_mult if r.scope == "level"}
    by_emp = {r.employee_id: r.multiplier for r in rows_mult if r.scope == "employee"}

    def mult(e):
        if e.id in by_emp:
            return by_emp[e.id]
        if e.hierarchy_level_id in by_level:
            return by_level[e.hierarchy_level_id]
        return glob if glob is not None else Decimal("1")

    # growth & activity KPI signals (PART 6)
    mdefs = list(MetricDefinition.objects.filter(status="active"))
    growth_defs = [m for m in mdefs if m.category == "growth"]
    activity_defs = [m for m in mdefs if m.category == "activity"]
    leaf = _leaf_stats(growth_defs + activity_defs, month, year)

    # ---- raw per-employee signals
    raw = {}
    for e in emps:
        revenue = by_user.get(e.user_id, 0.0)
        target = float(e.monthly_ctc(month, year) * mult(e))
        attain = min(100.0, revenue / target * 100) if target else 0.0
        raw[e.id] = {
            "revenue": revenue,
            "attain": attain,
            "growth": [leaf.get((e.id, m.id), (0.0, 0))[0] for m in growth_defs],
            "activity": [leaf.get((e.id, m.id), (0.0, 0))[0] for m in activity_defs],
        }

    # ---- peer peaks for normalisation
    rev_peak = max((raw[e.id]["revenue"] for e in emps), default=0.0)
    growth_peaks = [max((raw[e.id]["growth"][i] for e in emps), default=0.0)
                    for i in range(len(growth_defs))]
    activity_peaks = [max((raw[e.id]["activity"][i] for e in emps), default=0.0)
                      for i in range(len(activity_defs))]

    rows = []
    for e in emps:
        r = raw[e.id]
        rev_score = round((_norm(r["revenue"], rev_peak) + r["attain"]) / 2, 1)
        g = [_norm(r["growth"][i], growth_peaks[i]) for i in range(len(growth_defs))]
        a = [_norm(r["activity"][i], activity_peaks[i]) for i in range(len(activity_defs))]
        growth_score = round(sum(g) / len(g), 1) if g else 0.0
        activity_score = round(sum(a) / len(a), 1) if a else 0.0
        wr, wg, wa = PerformanceWeight.resolve(e)
        overall = round(rev_score * wr + growth_score * wg + activity_score * wa, 1)
        rows.append({
            "id": e.id, "user_id": e.user_id, "manager_id": e.manager_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "revenue_generated": round(r["revenue"], 2),
            "target_attainment": round(r["attain"], 1),
            "revenue_score": rev_score,
            "growth_score": growth_score,
            "activity_score": activity_score,
            "overall": overall,
            "weights": {"revenue": round(wr * 100), "growth": round(wg * 100), "activity": round(wa * 100)},
        })

    rows.sort(key=lambda x: x["overall"], reverse=True)
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return {"month": month, "year": year, "rows": rows}


def scoped_performance(user, data):
    """Admins / Finance / HR see everyone; a manager sees their subtree + self."""
    from apps.accounts.access import is_admin_view
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data

    children = {}
    for r in data["rows"]:
        children.setdefault(r["manager_id"], []).append(r["user_id"])

    keep, stack = set(), [user.id]
    while stack:
        uid = stack.pop()
        if uid in keep:
            continue
        keep.add(uid)
        stack.extend(children.get(uid, []))

    filtered = [r for r in data["rows"] if r["user_id"] in keep]
    filtered.sort(key=lambda x: x["overall"], reverse=True)
    out = []
    for i, r in enumerate(filtered, 1):
        rr = dict(r)
        rr["rank"] = i
        out.append(rr)
    return {"month": data["month"], "year": data["year"], "rows": out}
