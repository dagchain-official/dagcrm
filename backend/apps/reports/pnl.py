"""P&L Engine (PART 4) — derived, no new tables.

Profit = Revenue − Cost, rolled up the org tree (manager chain from PART 2):
  RM profit = own;  TL profit = self + reports;  SM/BH inherit upward.

Revenue is attributed to the customer's owner: customer.assigned_to if set (a
reassigned customer), else the originating lead's assignee (customer -> lead ->
assigned_to). Revenue with no owner is NOT lost — it surfaces as "unattributed".
Cost = monthly CTC (PART 3: salary + extra costs). net_revenue is used so a
partner commission is never double-counted.
"""
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.hr.models import Employee
from apps.sales.models import Revenue


def _revenue_by_user(month, year):
    rows = (Revenue.objects.filter(created_at__year=year, created_at__month=month)
            .annotate(owner=Coalesce("customer__assigned_to", "customer__lead__assigned_to"))
            .values("owner")
            .annotate(t=Sum("net_revenue")))
    by_user, unattributed = {}, 0.0
    for r in rows:
        uid = r["owner"]
        amt = float(r["t"] or 0)
        if uid:
            by_user[uid] = by_user.get(uid, 0.0) + amt
        else:
            unattributed += amt
    return by_user, unattributed


def compute_pnl(month, year):
    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    reports = {}                         # manager_user_id -> [Employee]
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}
    by_user, unattributed = _revenue_by_user(month, year)

    def node(e, seen):
        if e.id in seen:                 # cycle guard (A->B->A)
            return None
        seen = seen | {e.id}
        own_rev = by_user.get(e.user_id, 0.0)
        own_cost = float(e.monthly_ctc(month, year))
        kids = sorted(reports.get(e.user_id, []),
                      key=lambda x: x.hierarchy_level.level_order if x.hierarchy_level else 999)
        children, sub_rev, sub_cost = [], 0.0, 0.0
        for c in kids:
            cn = node(c, seen)
            if not cn:
                continue
            children.append(cn)
            sub_rev += cn["revenue"]
            sub_cost += cn["cost"]
        rev, cost = own_rev + sub_rev, own_cost + sub_cost
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "own_revenue": round(own_rev, 2), "own_cost": round(own_cost, 2),
            "revenue": round(rev, 2), "cost": round(cost, 2),
            "profit": round(rev - cost, 2),
            "margin": round((rev - cost) / rev * 100, 1) if rev else 0,
            "reports": children,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    total_rev = round(sum(n["revenue"] for n in tree) + unattributed, 2)
    total_cost = round(sum(n["cost"] for n in tree), 2)
    return {
        "month": month, "year": year,
        "tree": tree,
        "unattributed_revenue": round(unattributed, 2),
        "company": {
            "revenue": total_rev, "cost": total_cost,
            "profit": round(total_rev - total_cost, 2),
        },
    }


def scoped_for(user, data):
    """Admins/Finance see everything; a manager sees only their own subtree."""
    from apps.accounts.access import is_admin_view
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role == "Finance":
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
        "unattributed_revenue": 0,
        "company": {"revenue": mine["revenue"], "cost": mine["cost"],
                    "profit": mine["profit"]} if mine else
                   {"revenue": 0, "cost": 0, "profit": 0},
    }
