"""DAGChain — per-RM book: each employee's assigned DAGChain users with their
nodes, node spend (revenue), rewards, staked, DGC balance and referrals.
Mirrors the FX Artha "Lots & Commission" report and is scoped the same way
(admins/Finance/HR see all; a manager sees their subtree; an RM sees own).
"""
from collections import defaultdict

from django.db.models import Count, Q, Sum


def compute_dagchain_by_rm(employee_id=None):
    from apps.crm.models import Customer
    from apps.hr.models import Employee
    from apps.integrations.models import DagChainNode

    node_agg = {n["customer_id"]: n for n in DagChainNode.objects.values("customer_id").annotate(
        val=Count("id", filter=Q(kind="validator")),
        sto=Count("id", filter=Q(kind="storage")),
        spend=Sum("purchase_price"), rewards=Sum("rewards_earned"),
        staked=Sum("staked_amount"))}

    # the super admin is never surfaced as an owner anywhere
    emp_by_user = {e.user_id: e for e in
                   Employee.objects.select_related("user").exclude(user__is_superuser=True)}
    custs = Customer.objects.filter(dagchain__isnull=False).select_related("assigned_to", "dagchain")

    by_emp, emp_meta = defaultdict(list), {}
    for c in custs:
        owner = c.assigned_to if (c.assigned_to_id and not c.assigned_to.is_superuser) else None
        emp = emp_by_user.get(owner.id) if owner else None
        if employee_id and (not emp or emp.id != employee_id):
            continue
        key = emp.id if emp else 0
        emp_meta[key] = (getattr(owner, "id", None), getattr(owner, "name", None) or "Unassigned")
        prof, na = c.dagchain, node_agg.get(c.id, {})
        by_emp[key].append({
            "customer_id": c.id, "customer_name": c.name,
            "validator_nodes": na.get("val") or 0, "storage_nodes": na.get("sto") or 0,
            "node_spend": round(float(na.get("spend") or 0), 2),
            "rewards": round(float(na.get("rewards") or 0), 4),
            "staked": round(float(na.get("staked") or 0), 4),
            "dgc_balance": round(float(prof.dgc_balance or 0), 4),
            "referrals": prof.referral_count or 0,
            "ref_earnings": round(float(prof.total_referral_earnings or 0), 4),
        })

    def totals(rows, keys):
        return {k: round(sum(r[k] for r in rows), 2) for k in keys}

    ikeys = ["validator_nodes", "storage_nodes", "node_spend", "rewards", "staked",
             "dgc_balance", "referrals", "ref_earnings"]
    employees = []
    for key, rows in by_emp.items():
        rows.sort(key=lambda r: r["node_spend"], reverse=True)
        user_id, name = emp_meta[key]
        employees.append({"employee_id": key, "user_id": user_id, "name": name,
                          "customer_count": len(rows), "customers": rows, **totals(rows, ikeys)})
    employees.sort(key=lambda e: e["node_spend"], reverse=True)

    grand = totals(employees, ikeys)
    grand["customers"] = sum(e["customer_count"] for e in employees)
    return {"employees": employees, "grand": grand}


def scoped_dagchain_by_rm(user, data):
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data
    keep = set(subordinate_user_ids(user, include_self=True))
    emps = [e for e in data["employees"] if e["user_id"] in keep]
    ikeys = ["validator_nodes", "storage_nodes", "node_spend", "rewards", "staked",
             "dgc_balance", "referrals", "ref_earnings"]
    grand = {k: round(sum(e[k] for e in emps), 2) for k in ikeys}
    grand["customers"] = sum(e["customer_count"] for e in emps)
    return {"employees": emps, "grand": grand}
