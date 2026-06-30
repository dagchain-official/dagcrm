"""Formula Builder (PART 16) — admin-defined incentive rules, no code, no eval.

A rule is structured: 1..N conditions (AND/OR) over NAMED variables, plus a
payout. Variables are exposed by the other engines, so formulas compose the
whole system safely:

  revenue, cost, target, attainment, profit   (Parts 3/4/5)
  kpi:<key>                                    (Part 6 metrics)

Examples the builder expresses: "Revenue > Cost × 2 → 10% of revenue",
"kpi:new-users > 50 → $500 flat", "kpi:lots-traded > 100 → $2 per unit".
Subsumes multi-condition incentives (Part 15) through AND/OR matching.
"""
from decimal import Decimal

from apps.crm.models import MetricDefinition
from apps.hr.models import (
    Employee, FormulaCondition, FormulaRule, Incentive, Payroll, TargetMultiplier,
)

from .metrics import _leaf_stats
from .pnl import _revenue_by_user

VAR_LABELS = {
    "revenue": "Revenue", "cost": "Cost (CTC)", "target": "Target",
    "attainment": "Attainment %", "profit": "Profit",
}
_OP_SYM = dict(FormulaCondition.OPS)


def variable_options():
    opts = [{"key": k, "label": v} for k, v in VAR_LABELS.items()]
    for m in MetricDefinition.objects.filter(status="active"):
        opts.append({"key": f"kpi:{m.key}", "label": f"KPI · {m.name}"})
    return opts


def var_label(key):
    if key in VAR_LABELS:
        return VAR_LABELS[key]
    if key and key.startswith("kpi:"):
        return f"KPI {key[4:]}"
    return key or "?"


def rule_label(rule):
    parts = []
    for c in rule.conditions.all():
        if c.operator == "between":
            rhs = f"{c.right_value}–{c.right_value2}"
        elif c.right_type == "variable":
            rhs = var_label(c.right_variable)
            if float(c.right_factor) != 1:
                rhs += f" × {c.right_factor}"
        else:
            rhs = f"{c.right_value}"
        parts.append(f"{var_label(c.left)} {_OP_SYM.get(c.operator, c.operator)} {rhs}")
    cond = (" AND " if rule.match == "all" else " OR ").join(parts) or "always"
    if rule.payout_type == "percent":
        action = f"{rule.payout_value}% of {var_label(rule.payout_on)}"
    elif rule.payout_type == "per_unit":
        action = f"{rule.payout_value} per {var_label(rule.payout_on)}"
    else:
        action = f"${rule.payout_value} flat"
    return f"IF {cond} → {action}"


def _multiplier(emps):
    rows = list(TargetMultiplier.objects.filter(status="active"))
    glob = next((r.multiplier for r in rows if r.scope == "global"), Decimal("1"))
    by_level = {r.hierarchy_level_id: r.multiplier for r in rows if r.scope == "level"}
    by_emp = {r.employee_id: r.multiplier for r in rows if r.scope == "employee"}

    def m(e):
        if e.id in by_emp:
            return by_emp[e.id]
        if e.hierarchy_level_id in by_level:
            return by_level[e.hierarchy_level_id]
        return glob
    return m


def _build_context(month, year):
    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    by_user, _ = _revenue_by_user(month, year)
    mult = _multiplier(emps)
    metrics = list(MetricDefinition.objects.filter(status="active"))
    leaf = _leaf_stats(metrics, month, year) if metrics else {}

    ctx = {}
    for e in emps:
        revenue = by_user.get(e.user_id, 0.0)
        cost = float(e.monthly_ctc(month, year))
        target = cost * float(mult(e))
        c = {
            "revenue": revenue, "cost": cost, "target": target,
            "attainment": (revenue / target * 100) if target else 0.0,
            "profit": revenue - cost,
        }
        for m in metrics:
            c[f"kpi:{m.key}"] = leaf.get((e.id, m.id), (0.0, 0))[0]
        ctx[e.id] = c
    return emps, ctx


def _val(ctx, key):
    return float(ctx.get(key, 0.0))


def _eval_condition(c, ctx):
    left = _val(ctx, c.left)
    if c.operator == "between":
        lo = float(c.right_value)
        hi = float(c.right_value2) if c.right_value2 is not None else lo
        return lo <= left <= hi
    if c.right_type == "variable":
        right = _val(ctx, c.right_variable) * float(c.right_factor)
    else:
        right = float(c.right_value)
    return {
        "gt": left > right, "gte": left >= right, "lt": left < right,
        "lte": left <= right, "eq": left == right,
    }.get(c.operator, False)


def _eval_rule(rule, conds, ctx):
    results = [_eval_condition(c, ctx) for c in conds]
    matched = True if not results else (all(results) if rule.match == "all" else any(results))
    if not matched:
        return 0.0
    if rule.payout_type == "percent":
        return float(rule.payout_value) / 100 * _val(ctx, rule.payout_on)
    if rule.payout_type == "per_unit":
        return float(rule.payout_value) * _val(ctx, rule.payout_on)
    return float(rule.payout_value)          # flat


def compute_formulas(month, year):
    emps, ctx = _build_context(month, year)
    rules = list(FormulaRule.objects.filter(status="active").prefetch_related("conditions"))
    conds = {r.id: list(r.conditions.all()) for r in rules}
    labels = {r.id: rule_label(r) for r in rules}

    rows = []
    for e in emps:
        c = ctx[e.id]
        fired, total = [], 0.0
        for r in rules:
            amt = _eval_rule(r, conds[r.id], c)
            if amt:
                fired.append({"rule": r.name, "label": labels[r.id], "amount": round(amt, 2)})
                total += amt
        rows.append({
            "id": e.id, "user_id": e.user_id, "manager_id": e.manager_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "revenue": round(c["revenue"], 2), "cost": round(c["cost"], 2),
            "attainment": round(c["attainment"], 1),
            "fired": fired, "total": round(total, 2),
        })
    rows.sort(key=lambda x: x["total"], reverse=True)
    return {"month": month, "year": year, "rows": rows,
            "grand_total": round(sum(r["total"] for r in rows), 2)}


def scoped_formulas(user, data):
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


def run_formulas(month, year):
    """Persist formula payouts into Incentive (rule=null) + Payroll. Shares the
    computed-incentive slot with PART 14 — the most recent run wins."""
    data = compute_formulas(month, year)
    credited = payrolls = 0
    for r in data["rows"]:
        amount = Decimal(str(r["total"]))
        Incentive.objects.update_or_create(
            employee_id=r["id"], rule=None, month=month, year=year,
            defaults={"amount": amount})
        if amount:
            credited += 1
        pr = Payroll.objects.filter(employee_id=r["id"], month=month, year=year).first()
        if pr:
            pr.incentive = amount
            pr.save()
            payrolls += 1
    return {"month": month, "year": year, "employees_credited": credited,
            "payrolls_updated": payrolls, "grand_total": data["grand_total"]}
