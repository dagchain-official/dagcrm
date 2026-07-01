"""Business Contribution Engine (PART 12).

Net Business Contribution = Σ (component × admin-configured weight). Components
come from ContributionEntry (deposit, trading_loss, brokerage, insurance,
staking, other); the weights come from ContributionWeight (admin-defined, not
hardcoded — default: revenue +1, trading loss −1, deposit 0). Rolled up the
org tree.
"""
from django.db.models import Sum

from apps.crm.models import ContributionEntry, ContributionWeight
from apps.hr.models import Employee

COMPONENTS = ["deposit", "trading_loss", "brokerage", "insurance", "staking", "other"]


def _weights():
    w = ContributionWeight.objects.first()
    if w:
        return {c: float(getattr(w, c)) for c in COMPONENTS}
    return {"deposit": 0.0, "trading_loss": -1.0, "brokerage": 1.0,
            "insurance": 1.0, "staking": 1.0, "other": 1.0}


def compute_contribution(month, year):
    weights = _weights()
    agg = {}
    rows = (ContributionEntry.objects.filter(date__year=year, date__month=month)
            .values("employee_id")
            .annotate(**{c: Sum(c) for c in COMPONENTS}))
    for r in rows:
        agg[r["employee_id"]] = {c: float(r[c] or 0) for c in COMPONENTS}

    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    reports = {}
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}

    def node(e, seen):
        if e.id in seen:
            return None
        seen = seen | {e.id}
        comp = dict(agg.get(e.id, {c: 0.0 for c in COMPONENTS}))
        kids = sorted(reports.get(e.user_id, []),
                      key=lambda x: x.hierarchy_level.level_order if x.hierarchy_level else 999)
        children = [n for n in (node(c, seen) for c in kids) if n]
        for c in children:
            for k in COMPONENTS:
                comp[k] += c["components"][k]
        net = sum(comp[k] * weights[k] for k in COMPONENTS)
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "is_manager": bool(children),
            "components": {k: round(comp[k], 2) for k in COMPONENTS},
            "net_contribution": round(net, 2),
            "reports": children,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    company_net = round(sum(n["net_contribution"] for n in tree), 2)
    return {"month": month, "year": year, "tree": tree, "weights": weights,
            "company": {"net_contribution": company_net}}


def scoped_contribution(user, data):
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
        "month": data["month"], "year": data["year"], "weights": data["weights"],
        "tree": [mine] if mine else [],
        "company": {"net_contribution": mine["net_contribution"] if mine else 0},
    }
