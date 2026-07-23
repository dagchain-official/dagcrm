"""DAGChain — per-RM book: each employee's assigned DAGChain users with their
nodes, node spend (revenue), commission, rewards, staked, DGC balance and
referrals. Mirrors the FX Artha "Lots & Commission" report and is scoped the
same way (admins/Finance/HR see all; a manager sees their subtree; an RM sees own).

Commission runs on THREE separate bases, each with its own rate: validator node
purchases, storage node purchases, and staked DGC. The two node rates pay out in
money; the staking rate pays out in DGC, so it is reported in its own column and
never added into the money total.
"""
from collections import defaultdict

from django.db.models import Count, Q, Sum


SUM_KEYS = ["validator_nodes", "storage_nodes", "node_spend", "validator_spend",
            "storage_spend", "comm_validator", "comm_storage", "commission",
            "comm_staking", "rewards", "staked", "dgc_balance", "referrals",
            "ref_earnings"]


def _rates(override=None):
    """Configured commission rates, with an optional per-request preview override."""
    from apps.integrations.models import DagChainCommissionRate
    cfg = DagChainCommissionRate.get_solo()
    out = {"validator_pct": float(cfg.validator_pct), "storage_pct": float(cfg.storage_pct),
           "staking_pct": float(cfg.staking_pct)}
    for k, v in (override or {}).items():
        if k in out and v not in (None, ""):
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                pass
    return out


def compute_dagchain_by_rm(employee_id=None, rate_override=None):
    from apps.crm.models import Customer
    from apps.hr.models import Employee
    from apps.integrations.models import DagChainNode

    rates = _rates(rate_override)
    v_pct, s_pct, st_pct = (rates["validator_pct"] / 100, rates["storage_pct"] / 100,
                            rates["staking_pct"] / 100)

    node_agg = {n["customer_id"]: n for n in DagChainNode.objects.values("customer_id").annotate(
        val=Count("id", filter=Q(kind="validator")),
        sto=Count("id", filter=Q(kind="storage")),
        spend=Sum("purchase_price"), rewards=Sum("rewards_earned"),
        staked=Sum("staked_amount"),
        # split by kind — a validator and a storage node pay different commission
        val_spend=Sum("purchase_price", filter=Q(kind="validator")),
        sto_spend=Sum("purchase_price", filter=Q(kind="storage")))}

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
        val_spend = float(na.get("val_spend") or 0)
        sto_spend = float(na.get("sto_spend") or 0)
        staked = float(na.get("staked") or 0)
        comm_validator = val_spend * v_pct
        comm_storage = sto_spend * s_pct
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
    return {"employees": employees, "grand": grand, "rates": rates}


def scoped_dagchain_by_rm(user, data):
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data
    keep = set(subordinate_user_ids(user, include_self=True))
    emps = [e for e in data["employees"] if e["user_id"] in keep]
    grand = {k: round(sum(e[k] for e in emps), 2) for k in SUM_KEYS}
    grand["customers"] = sum(e["customer_count"] for e in emps)
    return {"employees": emps, "grand": grand, "rates": data.get("rates", {})}
