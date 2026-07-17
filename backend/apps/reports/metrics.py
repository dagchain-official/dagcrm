"""KPI / Metric Engine (PART 6) — generic, admin-configurable KPIs.

Per employee, per metric, for a month: a (value, weight) pair is computed from
either manual MetricEntry rows or a derived CRM signal. These roll up the org
tree AGGREGATION-AWARE:

  sum / count  -> additive (team = sum of members)
  average      -> count-weighted mean across the subtree (NOT a sum)
  latest       -> additive snapshot total (team = sum of each member's latest)

`weight` = number of underlying entries; it is what makes the average roll up
correctly. Revenue is deliberately NOT a metric here — it lives in sales.Revenue.
"""
from collections import defaultdict

from django.db.models import Avg, Count, Sum

from apps.crm.models import Lead, LeadActivity, MetricDefinition, MetricEntry
from apps.hr.models import Employee


def _combine(agg, parts):
    """parts = list of (value, weight). Combine per aggregation type."""
    total_w = sum(w for _, w in parts)
    if agg == "average":
        if not total_w:
            return (0.0, 0)
        return (sum(v * w for v, w in parts) / total_w, total_w)
    # sum / count / latest -> additive team total
    return (sum(v for v, _ in parts), total_w)


def _leaf_stats(mdefs, month, year, date_from=None, date_to=None):
    """(employee_id, metric_id) -> (value, weight) for the period.

    Period selection: a from/to date range wins; else month+year; else year-only;
    else (all None) it is CUMULATIVE (no date filter)."""
    def _flt(field, is_dt):
        if date_from or date_to:
            pre = f"{field}__date" if is_dt else field
            k = {}
            if date_from:
                k[f"{pre}__gte"] = date_from
            if date_to:
                k[f"{pre}__lte"] = date_to
            return k
        k = {}
        if year:
            k[f"{field}__year"] = year
        if month:
            k[f"{field}__month"] = month
        return k

    stats = defaultdict(lambda: (0.0, 0))
    manual = [m for m in mdefs if m.source == "manual"]
    derived = [m for m in mdefs if m.source == "derived"]

    # ---- manual metrics: aggregate MetricEntry rows
    if manual:
        agg_of = {m.id: m.aggregation for m in manual}
        non_latest = [m.id for m in manual if m.aggregation != "latest"]
        if non_latest:
            rows = (MetricEntry.objects
                    .filter(metric_id__in=non_latest, **_flt("date", False))
                    .values("metric_id", "employee_id")
                    .annotate(s=Sum("value"), c=Count("id"), a=Avg("value")))
            for r in rows:
                mid, eid, c = r["metric_id"], r["employee_id"], r["c"]
                agg = agg_of[mid]
                if agg == "sum":
                    stats[(eid, mid)] = (float(r["s"] or 0), c)
                elif agg == "count":
                    stats[(eid, mid)] = (float(c), c)
                elif agg == "average":
                    stats[(eid, mid)] = (float(r["a"] or 0), c)
        latest_ids = [m.id for m in manual if m.aggregation == "latest"]
        if latest_ids:
            seen = set()
            for e in (MetricEntry.objects
                      .filter(metric_id__in=latest_ids, **_flt("date", False))
                      .order_by("metric_id", "employee_id", "-date", "-id")
                      .values("metric_id", "employee_id", "value")):
                k = (e["employee_id"], e["metric_id"])
                if k in seen:
                    continue
                seen.add(k)
                stats[k] = (float(e["value"] or 0), 1)

    # ---- derived metrics: count existing CRM signals, attributed via the
    #      lead owner (lead.assigned_to -> their Employee) — same path as P&L.
    if derived:
        u2e = dict(Employee.objects.values_list("user_id", "id"))
        for m in derived:
            if m.derived_key in ("lead_activity:meeting", "lead_activity:call"):
                atype = m.derived_key.split(":")[1]
                rows = (LeadActivity.objects
                        .filter(activity_type=atype, **_flt("created_at", True))
                        .values("lead__assigned_to").annotate(c=Count("id")))
                for r in rows:
                    eid = u2e.get(r["lead__assigned_to"])
                    if eid:
                        stats[(eid, m.id)] = (float(r["c"]), r["c"])
            elif m.derived_key == "lead:converted":
                # credit the month the lead was CONVERTED (not created)
                rows = (Lead.objects.pipeline()
                        .filter(status="converted", **_flt("converted_at", True))
                        .values("assigned_to").annotate(c=Count("id")))
                for r in rows:
                    eid = u2e.get(r["assigned_to"])
                    if eid:
                        stats[(eid, m.id)] = (float(r["c"]), r["c"])
    return stats


def compute_kpis(month, year, business_id=None, date_from=None, date_to=None):
    mdefs = list(MetricDefinition.objects.filter(status="active").select_related("business"))
    if business_id:
        mdefs = [m for m in mdefs if m.business_id in (business_id, None)]
    leaf = _leaf_stats(mdefs, month, year, date_from, date_to)

    emps = list(Employee.objects.select_related("user", "hierarchy_level")
                .exclude(user__is_superuser=True))
    reports = {}
    for e in emps:
        reports.setdefault(e.manager_id, []).append(e)
    user_ids = {e.user_id for e in emps}

    def node(e, seen):
        if e.id in seen:                  # cycle guard
            return None
        seen = seen | {e.id}
        kids = sorted(reports.get(e.user_id, []),
                      key=lambda x: x.hierarchy_level.level_order if x.hierarchy_level else 999)
        child_nodes = [n for n in (node(c, seen) for c in kids) if n]
        rolled = {}
        for m in mdefs:
            parts = [leaf.get((e.id, m.id), (0.0, 0))] + [c["_stats"][m.id] for c in child_nodes]
            rolled[m.id] = _combine(m.aggregation, parts)
        return {
            "id": e.id, "user_id": e.user_id,
            "name": e.user.name if e.user else "—",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
            "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
            "is_manager": bool(child_nodes),
            "values": {m.id: round(rolled[m.id][0], 2) for m in mdefs},
            "_stats": rolled,             # internal (value, weight) for rollup
            "reports": child_nodes,
        }

    roots = [e for e in emps if not e.manager_id or e.manager_id not in user_ids]
    tree = [n for n in (node(e, set()) for e in roots) if n]
    tree.sort(key=lambda n: n["level_order"])

    company = {m.id: round(_combine(m.aggregation, [n["_stats"][m.id] for n in tree])[0], 2)
               for m in mdefs}

    def strip(ns):
        for n in ns:
            n.pop("_stats", None)
            strip(n["reports"])
    strip(tree)

    return {
        "month": month, "year": year,
        "metrics": [{"id": m.id, "name": m.name, "key": m.key, "unit": m.unit,
                     "aggregation": m.aggregation, "category": m.category,
                     "business": m.business.name if m.business_id else None} for m in mdefs],
        "tree": tree,
        "company": company,
    }


def scoped_kpis(user, data):
    """Admins / Finance / HR see everyone; anyone else sees their own subtree."""
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
        "metrics": data["metrics"],
        "tree": [mine] if mine else [],
        "company": mine["values"] if mine else {},
    }
