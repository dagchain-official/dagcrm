"""Target Engine (PART 5) — derived, only TargetMultiplier is a new table.

Per-employee target = monthly CTC (PART 3) × multiplier (TargetMultiplier).
Multiplier resolves employee > hierarchy-level > global (default 1.0).

A manager's HEADLINE target = the SUM of their whole team's individual targets
(their own personal target is NOT folded in). Achieved mirrors the same set so
team-target vs team-achieved compare apples-to-apples. A leaf (RM) shows their
own target/achieved.

Revenue attribution reuses the P&L path: customer -> lead -> assigned_to.
"""
from decimal import Decimal

from apps.hr.models import Employee, TargetMultiplier

from .pnl import _revenue_by_user


def _multiplier_resolver():
    """Pre-load active multipliers once → O(1) per-employee resolution."""
    rows = list(TargetMultiplier.objects.filter(status="active"))
    glob = next((r.multiplier for r in rows if r.scope == "global"), Decimal("1"))
    by_level = {r.hierarchy_level_id: r.multiplier for r in rows if r.scope == "level"}
    by_emp = {r.employee_id: r.multiplier for r in rows if r.scope == "employee"}

    def resolve(emp):
        if emp.id in by_emp:
            return by_emp[emp.id]
        if emp.hierarchy_level_id in by_level:
            return by_level[emp.hierarchy_level_id]
        return glob
    return resolve


def compute_targets(month, year):
    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    reports = {}                          # manager_user_id -> [Employee]
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}
    by_user, _ = _revenue_by_user(month, year)
    resolve = _multiplier_resolver()
    ctc = {e.id: e.monthly_ctc(month, year) for e in emps}   # one CTC calc per employee

    def own_target(e):
        return float(ctc[e.id] * resolve(e))

    def node(e, seen):
        if e.id in seen:                  # cycle guard (A->B->A)
            return None
        seen = seen | {e.id}
        o_target = own_target(e)
        o_ach = by_user.get(e.user_id, 0.0)
        kids = sorted(reports.get(e.user_id, []),
                      key=lambda x: x.hierarchy_level.level_order if x.hierarchy_level else 999)
        children, team_target, team_ach = [], 0.0, 0.0
        for c in kids:
            cn = node(c, seen)
            if not cn:
                continue
            children.append(cn)
            # subtree sum of INDIVIDUAL targets = child's own + the child's team
            team_target += cn["own_target"] + cn["team_target"]
            team_ach += cn["own_achieved"] + cn["team_achieved"]
        has_team = bool(children)
        target = team_target if has_team else o_target
        achieved = team_ach if has_team else o_ach
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "multiplier": float(resolve(e)),
            "ctc": round(float(ctc[e.id]), 2),
            "own_target": round(o_target, 2), "own_achieved": round(o_ach, 2),
            "team_target": round(team_target, 2), "team_achieved": round(team_ach, 2),
            "is_manager": has_team,
            "target": round(target, 2), "achieved": round(achieved, 2),
            "progress": round(min(100, achieved / target * 100), 1) if target else 0,
            "reports": children,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    total_target = round(sum(own_target(e) for e in emps), 2)
    total_ach = round(sum(by_user.get(e.user_id, 0.0) for e in emps), 2)
    return {
        "month": month, "year": year,
        "tree": tree,
        "company": {
            "target": total_target, "achieved": total_ach,
            "progress": round(min(100, total_ach / total_target * 100), 1) if total_target else 0,
        },
    }


def scoped_targets(user, data):
    """Admins / Finance / HR see everyone; anyone else sees only their own node
    (a manager → their subtree, an RM → just themselves)."""
    from apps.accounts.access import is_admin_view
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data

    emp_id = Employee.objects.filter(user=user).values_list("id", flat=True).first()

    def find(nodes):
        for n in nodes:
            if n["id"] == emp_id:
                return n
            hit = find(n["reports"])
            if hit:
                return hit
        return None

    mine = find(data["tree"]) if emp_id else None
    return {
        "month": data["month"], "year": data["year"],
        "tree": [mine] if mine else [],
        "company": {"target": mine["target"], "achieved": mine["achieved"],
                    "progress": mine["progress"]} if mine else
                   {"target": 0, "achieved": 0, "progress": 0},
    }
