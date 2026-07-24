"""Commission rules — the single source for per-product commission rates.

Rates are set per product with an optional per-RM override (see
integrations.CommissionRule). This module loads them once and resolves the
effective rate for an (employee, product) pair, and lists the products that can
carry a rate so the config UI can build its matrix.

Commission is computed LIVE from these rates wherever it's shown (Traders & Lots,
DAGChain per-RM, the account drill-downs), so changing a rate applies to every
existing record immediately — no backfill step.
"""
from collections import defaultdict


def load_rules(platform):
    """(universal, overrides) for a platform.
    universal[product_key] -> rate ; overrides[employee_id][product_key] -> rate.
    """
    from apps.integrations.models import CommissionRule
    universal, overrides = {}, defaultdict(dict)
    for r in CommissionRule.objects.filter(platform=platform):
        if r.employee_id is None:
            universal[r.product_key] = float(r.rate)
        else:
            overrides[r.employee_id][r.product_key] = float(r.rate)
    return universal, overrides


def rate_for(universal, overrides, product_key, employee_id, fallback=0.0):
    """The RM's override if they have one, else the universal rate, else fallback."""
    emp_over = overrides.get(employee_id)
    if emp_over and product_key in emp_over:
        return emp_over[product_key]
    return universal.get(product_key, fallback)


def fxartha_lots_universal():
    """Universal per-lot rate: the commission rule if set, else the legacy
    Activity-Incentive lots rate so nothing changes until a rule is entered."""
    universal, _ = load_rules("fxartha")
    if "lots" in universal:
        return universal["lots"]
    from .traders import lots_rate
    return lots_rate()


# FX Artha's built-in commissionable bases. "amount" = a $ per lot; "percent" =
# a percent of that money base (brokerage, net deposit). Each computes from data
# the sync already stores per trader.
FXARTHA_BASES = [
    {"key": "lots", "label": "Lots", "unit": "$ / lot", "basis": "amount"},
    {"key": "brokerage", "label": "Brokerage", "unit": "% of brokerage", "basis": "percent"},
    {"key": "deposit", "label": "Deposit", "unit": "% of net deposit", "basis": "percent"},
]
_FX_BUILTIN = {b["key"] for b in FXARTHA_BASES}


def fxartha_products():
    universal, _ = load_rules("fxartha")
    out = [{**b, "rate": universal.get(b["key"], 0.0)} for b in FXARTHA_BASES]
    # anything the admin added by hand (a custom base) — kept so its rate persists
    for k, v in sorted(universal.items()):
        if k not in _FX_BUILTIN:
            out.append({"key": k, "label": k, "unit": "$ / lot", "basis": "amount",
                        "rate": v, "custom": True})
    return out


def dagchain_products():
    """DAGChain products that can carry a rate: every DISTINCT node package
    actually present (matched on the node, not the catalogue), grouped by kind,
    plus staking, plus any package an admin added by hand (e.g. a tier not yet
    sold). Each carries its current universal rate."""
    from apps.integrations.models import DagChainNode
    universal, _ = load_rules("dagchain")
    out, seen = [], set()
    for kind in ("validator", "storage"):
        pkgs = (DagChainNode.objects.filter(kind=kind).exclude(package="")
                .values_list("package", flat=True).distinct().order_by("package"))
        for pkg in pkgs:
            seen.add(pkg)
            out.append({"key": pkg, "label": pkg, "kind": kind, "unit": "% of price",
                        "rate": universal.get(pkg, 0.0)})
    out.append({"key": "staking", "label": "Staking", "kind": "staking",
                "unit": "% of DGC", "rate": universal.get("staking", 0.0)})
    seen.add("staking")
    for k, v in sorted(universal.items()):
        if k not in seen:
            out.append({"key": k, "label": k, "kind": "custom", "unit": "% of price",
                        "rate": v, "custom": True})
    return out


def commission_products():
    """All settable commission products, per platform, with their universal rate."""
    return {"fxartha": fxartha_products(), "dagchain": dagchain_products()}
