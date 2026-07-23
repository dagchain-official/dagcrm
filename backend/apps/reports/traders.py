"""Traders & Lots report — per employee, the traders (customers) they own and
how many lots each has traded (this month + all-time), with an estimated
per-lot commission.

The book is built from the RM's ASSIGNED traders, not from the lots rows: a
trader who hasn't traded yet is still on their RM's book and belongs in the
count, showing 0 lots. Lots come from the "Lots Traded" MetricEntry rows
(populated by the FXArtha sync). Rate defaults to the active ActivityIncentive
on the lots metric (PART 14), overridable via ?rate=.

The commission here is an ESTIMATE for the book view. Actual incentive payouts
are computed by the incentive run from the employee stamped on each metric row,
so reassigning a trader never rewrites what someone was already paid.
"""
from collections import defaultdict

from apps.crm.models import MetricDefinition, MetricEntry
from apps.hr.models import ActivityIncentive


def _lots_metric_ids():
    return list(MetricDefinition.objects.filter(name__icontains="lot").values_list("id", flat=True))


def lots_rate():
    """Per-lot payout from the active Activity Incentive on a lots metric, else 0."""
    mids = _lots_metric_ids()
    ai = (ActivityIncentive.objects.filter(status="active", metric_id__in=mids)
          .order_by("id").first())
    return float(ai.rate) if ai else 0.0


def compute_traders_lots(month, year, rate=None, employee_id=None):
    from apps.hr.models import Employee

    from .fxartha import _fxartha_customers

    mids = _lots_metric_ids()
    rate = lots_rate() if rate is None else float(rate)

    # lots per trader, whoever recorded them — the book follows the trader
    tot, mon = defaultdict(float), defaultdict(float)
    if mids:
        for r in (MetricEntry.objects.filter(metric_id__in=mids, customer__isnull=False)
                  .values("customer_id", "value", "date")):
            v = float(r["value"] or 0)
            tot[r["customer_id"]] += v
            d = r["date"]
            if d and d.month == month and d.year == year:
                mon[r["customer_id"]] += v

    # the super admin is never surfaced as an owner anywhere
    emp_by_user = {e.user_id: e for e in
                   Employee.objects.select_related("user").exclude(user__is_superuser=True)}

    by_emp, emp_meta = defaultdict(list), {}
    for c in _fxartha_customers().select_related("assigned_to"):
        owner = c.assigned_to if (c.assigned_to_id and not c.assigned_to.is_superuser) else None
        emp = emp_by_user.get(owner.id) if owner else None
        if employee_id and (not emp or emp.id != employee_id):
            continue
        key = emp.id if emp else 0
        emp_meta[key] = (getattr(owner, "id", None), getattr(owner, "name", None) or "Unassigned")
        lm, lt = mon.get(c.id, 0.0), tot.get(c.id, 0.0)
        by_emp[key].append({
            "customer_id": c.id, "customer_name": c.name,
            "lots_month": round(lm, 2), "lots_total": round(lt, 2),
            "commission_month": round(lm * rate, 2), "commission_total": round(lt * rate, 2),
        })

    employees = []
    for key, traders in by_emp.items():
        traders.sort(key=lambda t: t["lots_total"], reverse=True)
        lm = sum(t["lots_month"] for t in traders)
        lt = sum(t["lots_total"] for t in traders)
        user_id, name = emp_meta[key]
        employees.append({
            "employee_id": key, "user_id": user_id, "name": name,
            "trader_count": len(traders), "traders": traders,
            "lots_month": round(lm, 2), "lots_total": round(lt, 2),
            "commission_month": round(lm * rate, 2), "commission_total": round(lt * rate, 2),
        })
    employees.sort(key=lambda e: e["lots_total"], reverse=True)

    grand = {
        "traders": sum(e["trader_count"] for e in employees),
        "lots_month": round(sum(e["lots_month"] for e in employees), 2),
        "lots_total": round(sum(e["lots_total"] for e in employees), 2),
        "commission_month": round(sum(e["commission_month"] for e in employees), 2),
        "commission_total": round(sum(e["commission_total"] for e in employees), 2),
    }
    return {"month": month, "year": year, "rate": rate, "employees": employees, "grand": grand}


def scoped_traders_lots(user, data):
    """Admins / Finance / HR see everyone; a manager sees their subtree + self."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data
    keep = set(subordinate_user_ids(user, include_self=True))
    emps = [e for e in data["employees"] if e["user_id"] in keep]
    grand = {
        "traders": sum(e["trader_count"] for e in emps),
        "lots_month": round(sum(e["lots_month"] for e in emps), 2),
        "lots_total": round(sum(e["lots_total"] for e in emps), 2),
        "commission_month": round(sum(e["commission_month"] for e in emps), 2),
        "commission_total": round(sum(e["commission_total"] for e in emps), 2),
    }
    return {"month": data["month"], "year": data["year"], "rate": data["rate"],
            "employees": emps, "grand": grand}
