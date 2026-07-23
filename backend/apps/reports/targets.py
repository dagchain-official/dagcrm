"""Target Engine (PART 5) — derived, only TargetMultiplier is a new table.

Per-employee target = monthly CTC (PART 3) × multiplier (TargetMultiplier),
UNLESS a target was explicitly assigned for that month (Targets → Assign Target),
in which case the assigned value wins. Delete the assigned target and the board
falls straight back to the derived number — nothing is left stranded.

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


def assigned_targets(month, year, ctc_by_user):
    """user_id -> explicitly assigned revenue target covering this month.

    An individual assignment lands on that user. A team assignment is split
    across the team by CTC share — the value was derived from the team's summed
    CTC in the first place, so splitting it back that way reproduces each
    person's number and keeps the roll-up exact.
    """
    from calendar import monthrange
    from datetime import date

    from apps.accounts.models import Team, TeamMember
    from apps.crm.models import TargetAssignment

    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])
    out = {}
    rows = (TargetAssignment.objects
            .filter(target__target_type="revenue",
                    target__start_date__lte=last, target__end_date__gte=first)
            .select_related("target", "team")
            .order_by("target_id", "id"))        # a later assignment wins
    team_members = {}
    for a in rows:
        value = float(a.target.value or 0)
        if a.user_id:
            out[a.user_id] = value
            continue
        if not a.team_id:
            continue
        uids = team_members.get(a.team_id)
        if uids is None:
            uids = set(TeamMember.objects.filter(team_id=a.team_id)
                       .values_list("user_id", flat=True))
            leader = Team.objects.filter(id=a.team_id).values_list("leader_id", flat=True).first()
            if leader:
                uids.add(leader)
            team_members[a.team_id] = uids
        if not uids:
            continue
        total_ctc = sum(ctc_by_user.get(u, 0.0) for u in uids)
        for u in uids:
            share = (ctc_by_user.get(u, 0.0) / total_ctc) if total_ctc else 1.0 / len(uids)
            out[u] = value * share
    return out


def rollup_for_incentives(month, year):
    """Per-employee {target, revenue, is_manager} for the incentive run, with the
    org roll-up applied.

    A manager owns no customers, so revenue attributed directly to them is 0 —
    grading them on that reads as 0% attainment and hands them a deduction while
    their team is over target. They are measured on their TEAM instead: the sum
    of their reports' targets and revenue (plus anything they closed themselves).

    Unlike the board, a leaf with no assigned target falls back to CTC ×
    multiplier — a month where nobody set targets must not dock everyone's pay.
    """
    emps = list(Employee.objects.select_related("user").exclude(user__is_superuser=True))
    reports = {}
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}
    by_user, _ = _revenue_by_user(month, year)
    resolve = _multiplier_resolver()
    ctc = {e.id: float(e.monthly_ctc(month, year)) for e in emps}
    assigned = assigned_targets(month, year, {e.user_id: ctc[e.id] for e in emps})

    out = {}

    def walk(e, seen):
        """Returns this node's headline (target, revenue); the parent sums those."""
        if e.id in seen:                       # cycle guard (A->B->A)
            return 0.0, 0.0
        seen = seen | {e.id}
        team_t = team_r = 0.0
        kids = reports.get(e.user_id, [])
        for c in kids:
            t, r = walk(c, seen)
            team_t += t
            team_r += r
        has_team = bool(kids)
        own_r = by_user.get(e.user_id, 0.0)
        if e.user_id in assigned:              # an explicit target always wins
            target = assigned[e.user_id]
        elif has_team:
            target = team_t
        else:
            target = ctc[e.id] * float(resolve(e))
        revenue = team_r + own_r if has_team else own_r
        out[e.id] = {"target": target, "revenue": revenue, "is_manager": has_team}
        return target, revenue

    for e in (x for x in emps if not x.manager_id or x.manager_id not in user_ids):
        walk(e, set())
    for e in emps:                             # anyone stranded by a manager cycle
        out.setdefault(e.id, {
            "target": assigned.get(e.user_id) or ctc[e.id] * float(resolve(e)),
            "revenue": by_user.get(e.user_id, 0.0), "is_manager": False})
    return out


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
    assigned = assigned_targets(month, year, {e.user_id: float(ctc[e.id]) for e in emps})

    def node(e, seen):
        if e.id in seen:                  # cycle guard (A->B->A)
            return None
        seen = seen | {e.id}
        # NO assigned target = no target. CTC × multiplier is only what the
        # Assign Target form SUGGESTS; it is not a target until someone sets it,
        # so deleting the target really does clear the board.
        o_target = assigned.get(e.user_id, 0.0)
        suggested = float(ctc[e.id] * resolve(e))
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
        # a target assigned straight to this person is their headline, even if
        # they lead a team (that's what a "business" scope assignment means)
        if e.user_id in assigned:
            target = assigned[e.user_id]
        else:
            target = team_target if has_team else o_target
        achieved = team_ach if has_team else o_ach
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "multiplier": float(resolve(e)),
            "ctc": round(float(ctc[e.id]), 2),
            # what Assign Target would propose — shown greyed out, never counted
            "suggested": round(suggested, 2),
            "own_target": round(o_target, 2), "own_achieved": round(o_ach, 2),
            "team_target": round(team_target, 2), "team_achieved": round(team_ach, 2),
            "is_manager": has_team,
            # true = a target was actually assigned to this person
            "assigned": e.user_id in assigned,
            "target": round(target, 2), "achieved": round(achieved, 2),
            "progress": round(min(100, achieved / target * 100), 1) if target else 0,
            "reports": children,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    total_target = round(sum(assigned.get(e.user_id, 0.0) for e in emps), 2)
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
