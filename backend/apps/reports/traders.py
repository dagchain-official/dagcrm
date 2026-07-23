"""Traders & Lots report — per employee, the traders (customers) they own and
how many lots each has traded (this month + all-time), with an estimated
per-lot commission. Reads the "Lots Traded" MetricEntry rows (populated by the
FXArtha sync, attributed to the stamped employee). Rate defaults to the active
ActivityIncentive on the lots metric (PART 14), overridable via ?rate=.
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
    mids = _lots_metric_ids()
    rate = lots_rate() if rate is None else float(rate)
    empty = {"month": month, "year": year, "rate": rate, "employees": [],
             "grand": {"traders": 0, "lots_month": 0, "lots_total": 0,
                       "commission_month": 0, "commission_total": 0}}
    if not mids:
        return empty

    qs = (MetricEntry.objects.filter(metric_id__in=mids, employee__isnull=False,
                                     customer__isnull=False)
          .exclude(employee__user__is_superuser=True))   # never surface the super admin
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    rows = qs.values("employee_id", "employee__user_id", "employee__user__name",
                     "customer_id", "customer__name", "value", "date")

    tot, mon, emp_meta, cust_meta = defaultdict(float), defaultdict(float), {}, {}
    for r in rows:
        key = (r["employee_id"], r["customer_id"])
        v = float(r["value"] or 0)
        tot[key] += v
        d = r["date"]
        if d and d.month == month and d.year == year:
            mon[key] += v
        emp_meta[r["employee_id"]] = (r["employee__user_id"], r["employee__user__name"])
        cust_meta[r["customer_id"]] = r["customer__name"]

    by_emp = defaultdict(list)
    for (emp_id, cust_id), lt in tot.items():
        lm = mon.get((emp_id, cust_id), 0.0)
        by_emp[emp_id].append({
            "customer_id": cust_id, "customer_name": cust_meta.get(cust_id),
            "lots_month": round(lm, 2), "lots_total": round(lt, 2),
            "commission_month": round(lm * rate, 2), "commission_total": round(lt * rate, 2),
        })

    employees = []
    for emp_id, traders in by_emp.items():
        traders.sort(key=lambda t: t["lots_total"], reverse=True)
        lm = sum(t["lots_month"] for t in traders)
        lt = sum(t["lots_total"] for t in traders)
        user_id, name = emp_meta[emp_id]
        employees.append({
            "employee_id": emp_id, "user_id": user_id, "name": name,
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
