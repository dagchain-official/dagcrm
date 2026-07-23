"""Incentive Engine (PART 14) — two configurable models combined per employee.

Model 1  IncentiveSlab     — target-attainment tiers. The tier whose
                             [min_pct, max_pct) contains the employee's
                             attainment pays incentive_pct of revenue (or target).
Model 2  ActivityIncentive — per-unit reward on any PART 6 KPI (lots × $2,
                             meetings × $200, new users × $5 …).

Composes existing engines: revenue via P&L attribution, target via PART 5
(CTC × multiplier), activity values via PART 6 metric leaf stats. The payout
flows into the existing Incentive + Payroll tables (run_incentives).
"""
from decimal import Decimal

from apps.crm.models import MetricDefinition
from apps.hr.models import (
    ActivityIncentive, Employee, Incentive, IncentivePlan, IncentiveSlab, Payroll,
    TargetMultiplier,
)

from .metrics import _leaf_stats
from .pnl import _revenue_by_user
from .targets import assigned_targets


def _multiplier_resolver():
    rows = list(TargetMultiplier.objects.filter(status="active"))
    glob = next((r.multiplier for r in rows if r.scope == "global"), Decimal("1"))
    by_level = {r.hierarchy_level_id: r.multiplier for r in rows if r.scope == "level"}
    by_emp = {r.employee_id: r.multiplier for r in rows if r.scope == "employee"}

    def resolve(e):
        if e.id in by_emp:
            return by_emp[e.id]
        if e.hierarchy_level_id in by_level:
            return by_level[e.hierarchy_level_id]
        return glob
    return resolve


def _pick_slab(attainment, slabs):
    """First tier whose [min_pct, max_pct) contains attainment (%)."""
    for s in slabs:
        lo = float(s.min_pct)
        hi = float(s.max_pct) if s.max_pct is not None else float("inf")
        if lo <= attainment < hi:
            return s
    return None


def _pick_slab_json(attainment, slabs):
    """Same, but for a plan's inline slab tiers (list of dicts)."""
    for s in slabs or []:
        try:
            lo = float(s.get("min_pct") or 0)
            hi = float(s["max_pct"]) if s.get("max_pct") not in (None, "") else float("inf")
        except (TypeError, ValueError):
            continue
        if lo <= attainment < hi:
            return s
    return None


def _plan_amount(plan, revenue, target, attain):
    """A per-employee IncentivePlan → (incentive, deduction, label).
      met  (attain >= 100%): base (%/fixed/slab) + over_pct on revenue above target
      miss (attain < 100%) : deduction_pct of target
    """
    inc = ded = 0.0
    if attain >= 100:
        if plan.incentive_type == "percentage":
            inc = float(plan.incentive_value) / 100 * target
            label = f"met → {plan.incentive_value}% of target"
        elif plan.incentive_type == "fixed":
            inc = float(plan.incentive_value)
            label = f"met → ${plan.incentive_value} fixed"
        else:  # slab
            tier = _pick_slab_json(attain, plan.slabs)
            pct = float(tier.get("incentive_pct", 0)) if tier else 0.0
            inc = pct / 100 * revenue
            label = f"met → slab {pct}% of revenue"
        over_pct = float(plan.over_pct or 0)
        if over_pct and revenue > target:
            over = (revenue - target) * over_pct / 100
            inc += over
            label += f" + {over_pct}% on ${round(revenue - target):,} extra"
    else:
        ded_pct = float(plan.deduction_pct or 0)
        ded = ded_pct / 100 * target
        label = f"missed ({round(attain)}%) → −{ded_pct}% of target"
    return round(inc, 2), round(ded, 2), label


def compute_incentives(month, year):
    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    by_user, _ = _revenue_by_user(month, year)
    mult = _multiplier_resolver()
    # Attainment is measured against the target the person was ACTUALLY given.
    # Only when nothing was assigned do we fall back to CTC × multiplier —
    # otherwise a month with no target would read as 0% and trigger deductions.
    ctc = {e.id: float(e.monthly_ctc(month, year)) for e in emps}
    assigned = assigned_targets(month, year, {e.user_id: ctc[e.id] for e in emps})

    slabs = list(IncentiveSlab.objects.filter(status="active"))
    plans = {p.employee_id: p for p in IncentivePlan.objects.filter(month=month, year=year)}
    acts = list(ActivityIncentive.objects.filter(status="active").select_related("metric"))
    act_metrics = [a.metric for a in acts if a.metric.status == "active"]
    leaf = _leaf_stats(act_metrics, month, year) if act_metrics else {}

    rows = []
    for e in emps:
        revenue = by_user.get(e.user_id, 0.0)
        target = assigned.get(e.user_id) or ctc[e.id] * float(mult(e))
        attain = (revenue / target * 100) if target else 0.0

        # A per-employee IncentivePlan (set with the target) takes PRIORITY over
        # the global slab schedule; otherwise fall back to the global slabs.
        deduction = 0.0
        plan = plans.get(e.id)
        if plan:
            slab_amt, deduction, slab_label = _plan_amount(plan, revenue, target, attain)
        else:
            slab = _pick_slab(attain, slabs)
            slab_amt = 0.0
            slab_label = None
            if slab and slab.incentive_pct:
                base = revenue if slab.basis == "revenue" else target
                slab_amt = float(slab.incentive_pct) / 100 * base
                hi = f"{slab.max_pct}%" if slab.max_pct is not None else "∞"
                slab_label = f"{slab.min_pct}–{hi}% → {slab.incentive_pct}% of {slab.basis}"

        activities = []
        for a in acts:
            if a.metric.status != "active":
                continue
            value = leaf.get((e.id, a.metric_id), (0.0, 0))[0]
            if value < float(a.min_count):
                continue
            amt = value * float(a.rate)
            if amt:
                activities.append({"name": a.name, "metric": a.metric.name,
                                   "count": round(value, 2), "rate": float(a.rate),
                                   "amount": round(amt, 2)})

        act_total = sum(x["amount"] for x in activities)
        total = round(slab_amt + act_total - deduction, 2)   # deduction on target-miss
        rows.append({
            "id": e.id, "user_id": e.user_id, "manager_id": e.manager_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "revenue": round(revenue, 2), "target": round(target, 2),
            "attainment": round(attain, 1),
            "slab": slab_label, "slab_amount": round(slab_amt, 2),
            "deduction": round(deduction, 2), "has_plan": bool(plan),
            "activities": activities, "activity_amount": round(act_total, 2),
            "total": total,
        })

    rows.sort(key=lambda x: x["total"], reverse=True)
    return {"month": month, "year": year, "rows": rows,
            "grand_total": round(sum(r["total"] for r in rows), 2)}


def scoped_incentives(user, data):
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
    rows = [r for r in data["rows"] if r["user_id"] in keep]
    return {"month": data["month"], "year": data["year"], "rows": rows,
            "grand_total": round(sum(r["total"] for r in rows), 2)}


def run_incentives(month, year):
    """Persist computed totals into Incentive (rule=null) + that month's Payroll."""
    data = compute_incentives(month, year)
    credited = payrolls = 0
    for r in data["rows"]:
        amount = Decimal(str(r["total"]))
        Incentive.objects.update_or_create(
            employee_id=r["id"], rule=None, source="slab", month=month, year=year,
            defaults={"amount": amount})
        if amount:
            credited += 1
        pr = Payroll.objects.filter(employee_id=r["id"], month=month, year=year).first()
        if pr:
            pr.incentive = amount
            pr.save()                 # recomputes final_salary
            payrolls += 1
    return {"month": month, "year": year, "employees_credited": credited,
            "payrolls_updated": payrolls, "grand_total": data["grand_total"]}
