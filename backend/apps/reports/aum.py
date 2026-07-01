"""New AUM Engine (PART 11).

Per employee, for a month:
  Existing AUM  = cumulative (deposits − withdrawals) BEFORE the month
  New Deposits  = deposits in the month
  Withdrawals   = withdrawals in the month
  Net New AUM   = New Deposits − Withdrawals
  Closing AUM   = Existing + Net New

All additive → rolled up the org tree (RM → TL → Sales Manager → Business Head).
"""
import datetime

from django.db.models import Sum

from apps.crm.models import AumEntry
from apps.hr.models import Employee


def _sums(qs):
    """employee_id -> {deposit, withdrawal}"""
    out = {}
    for r in qs.values("employee_id", "entry_type").annotate(s=Sum("amount")):
        out.setdefault(r["employee_id"], {})[r["entry_type"]] = float(r["s"] or 0)
    return out


def compute_aum(month, year):
    start = datetime.date(year, month, 1)
    before = _sums(AumEntry.objects.filter(date__lt=start))
    inmonth = _sums(AumEntry.objects.filter(date__year=year, date__month=month))

    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    reports = {}
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}

    def own(e):
        b = before.get(e.id, {})
        m = inmonth.get(e.id, {})
        existing = b.get("deposit", 0.0) - b.get("withdrawal", 0.0)
        new_dep = m.get("deposit", 0.0)
        wd = m.get("withdrawal", 0.0)
        return existing, new_dep, wd

    def node(e, seen):
        if e.id in seen:
            return None
        seen = seen | {e.id}
        ex, nd, wd = own(e)
        kids = sorted(reports.get(e.user_id, []),
                      key=lambda x: x.hierarchy_level.level_order if x.hierarchy_level else 999)
        children = [n for n in (node(c, seen) for c in kids) if n]
        for c in children:
            ex += c["existing"]
            nd += c["new_deposits"]
            wd += c["withdrawals"]
        net = nd - wd
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "is_manager": bool(children),
            "existing": round(ex, 2), "new_deposits": round(nd, 2),
            "withdrawals": round(wd, 2), "net_new": round(net, 2),
            "closing": round(ex + net, 2),
            "reports": children,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    def total(key):
        return round(sum(n[key] for n in tree), 2)
    return {
        "month": month, "year": year, "tree": tree,
        "company": {"existing": total("existing"), "new_deposits": total("new_deposits"),
                    "withdrawals": total("withdrawals"), "net_new": total("net_new"),
                    "closing": total("closing")},
    }


def scoped_aum(user, data):
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
    keys = ["existing", "new_deposits", "withdrawals", "net_new", "closing"]
    return {
        "month": data["month"], "year": data["year"],
        "tree": [mine] if mine else [],
        "company": {k: mine[k] for k in keys} if mine else {k: 0 for k in keys},
    }
