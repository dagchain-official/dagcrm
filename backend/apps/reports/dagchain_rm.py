"""DAGChain — per-RM book: each employee's assigned DAGChain users with their
nodes, node spend (revenue), commission, rewards, staked, DGC balance and
referrals. Mirrors the FX Artha "Lots & Commission" report and is scoped the
same way (admins/Finance/HR see all; a manager sees their subtree; an RM sees own).

Commission is PER PRODUCT: each node pays its package's rate (percent of the
node's purchase price), with a per-RM override where set. Staking pays its own
rate (percent of the DGC staked). Node commission is money; staking commission
is DGC, so it stays in its own column and is never added into the money total.
"""
from collections import defaultdict

from django.db.models import Count, Q, Sum


SUM_KEYS = ["validator_nodes", "storage_nodes", "node_spend", "validator_spend",
            "storage_spend", "comm_validator", "comm_storage", "commission",
            "comm_staking", "rewards", "staked", "dgc_balance", "referrals",
            "ref_earnings"]


def compute_dagchain_by_rm(employee_id=None, rate_override=None):
    from apps.crm.models import Customer
    from apps.hr.models import Employee
    from apps.integrations.models import DagChainNode

    from .commission import load_rules, rate_for

    universal, overrides = load_rules("dagchain")

    # per-customer node roll-up, plus per-(customer, kind, package) spend so each
    # package can be paid at its own rate
    node_agg = {n["customer_id"]: n for n in DagChainNode.objects.values("customer_id").annotate(
        val=Count("id", filter=Q(kind="validator")),
        sto=Count("id", filter=Q(kind="storage")),
        spend=Sum("purchase_price"), rewards=Sum("rewards_earned"),
        staked=Sum("staked_amount"))}
    pkg_spend = defaultdict(lambda: defaultdict(float))   # customer_id -> {(kind,pkg): spend}
    for r in (DagChainNode.objects.exclude(package="")
              .values("customer_id", "kind", "package").annotate(s=Sum("purchase_price"))):
        pkg_spend[r["customer_id"]][(r["kind"], r["package"])] += float(r["s"] or 0)

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
        emp_id = emp.id if emp else None
        # each package paid at its own rate; unassigned (key 0) earns nothing
        val_spend = sto_spend = comm_validator = comm_storage = 0.0
        for (kind, pkg), spend in pkg_spend.get(c.id, {}).items():
            pct = rate_for(universal, overrides, pkg, emp_id) / 100 if emp_id else 0.0
            if kind == "validator":
                val_spend += spend
                comm_validator += spend * pct
            else:
                sto_spend += spend
                comm_storage += spend * pct
        # real contract staking from the profile (per-node stakedAmount is 0);
        # fall back to the node figure only if the profile has none
        staked = float(prof.staked_amount or 0) or float(na.get("staked") or 0)
        st_pct = rate_for(universal, overrides, "staking", emp_id) / 100 if emp_id else 0.0
        by_emp[key].append({
            "customer_id": c.id, "customer_name": c.name,
            "validator_nodes": na.get("val") or 0, "storage_nodes": na.get("sto") or 0,
            "node_spend": round(float(na.get("spend") or 0), 2),
            "validator_spend": round(val_spend, 2), "storage_spend": round(sto_spend, 2),
            "comm_validator": round(comm_validator, 2),
            "comm_storage": round(comm_storage, 2),
            "commission": round(comm_validator + comm_storage, 2),   # money
            "comm_staking": round(staked * st_pct, 4),               # DGC
            "rewards": round(float(na.get("rewards") or 0), 4),
            "staked": round(staked, 4),
            "dgc_balance": round(float(prof.dgc_balance or 0), 4),
            "referrals": prof.referral_count or 0,
            "ref_earnings": round(float(prof.total_referral_earnings or 0), 4),
        })

    def totals(rows, keys):
        return {k: round(sum(r[k] for r in rows), 2) for k in keys}

    employees = []
    for key, rows in by_emp.items():
        rows.sort(key=lambda r: r["node_spend"], reverse=True)
        user_id, name = emp_meta[key]
        employees.append({"employee_id": key, "user_id": user_id, "name": name,
                          "customer_count": len(rows), "customers": rows,
                          **totals(rows, SUM_KEYS)})
    employees.sort(key=lambda e: e["node_spend"], reverse=True)

    grand = totals(employees, SUM_KEYS)
    grand["customers"] = sum(e["customer_count"] for e in employees)
    return {"employees": employees, "grand": grand}


def scoped_dagchain_by_rm(user, data):
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data
    keep = set(subordinate_user_ids(user, include_self=True))
    emps = [e for e in data["employees"] if e["user_id"] in keep]
    grand = {k: round(sum(e[k] for e in emps), 2) for k in SUM_KEYS}
    grand["customers"] = sum(e["customer_count"] for e in emps)
    return {"employees": emps, "grand": grand}
