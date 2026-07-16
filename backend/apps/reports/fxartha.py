"""FXArtha Traders — one detailed row per synced trader (Customer), pulling all
FXArtha figures together: lots traded, brokerage/revenue, deposits, withdrawals,
net AUM, contribution components, the account date, and the owning RM.

Note: the FXArtha API gives cumulative totals per trader (no per-transaction
breakdown), so each trader's `date` is the account-opened date; the date filter
selects traders whose account falls in the range.
"""
from django.db.models import Q, Sum


def _lots_metric_ids():
    from apps.crm.models import MetricDefinition
    return list(MetricDefinition.objects.filter(name__icontains="lot").values_list("id", flat=True))


def compute_fxartha_traders(date_from=None, date_to=None, q=None):
    from apps.crm.models import AumEntry, ContributionEntry, Customer, MetricEntry
    from apps.sales.models import Revenue

    custs = (Customer.objects.exclude(external_id="")
             .select_related("assigned_to").order_by("name"))
    if q:
        custs = custs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))

    lot_ids = _lots_metric_ids()
    rows = []
    for c in custs:
        rev = Revenue.objects.filter(customer=c).aggregate(
            g=Sum("gross_revenue"), cm=Sum("commission"), n=Sum("net_revenue"))
        aum = AumEntry.objects.filter(customer=c)
        dep = aum.filter(entry_type="deposit").aggregate(s=Sum("amount"))["s"] or 0
        wd = aum.filter(entry_type="withdrawal").aggregate(s=Sum("amount"))["s"] or 0
        con = ContributionEntry.objects.filter(customer=c).aggregate(
            b=Sum("brokerage"), i=Sum("insurance"), s=Sum("staking"), tl=Sum("trading_loss"))
        lots = (MetricEntry.objects.filter(customer=c, metric_id__in=lot_ids)
                .aggregate(s=Sum("value"))["s"] or 0) if lot_ids else 0

        # representative date = latest entry date across the trader's synced rows
        dts = []
        d = ContributionEntry.objects.filter(customer=c).values_list("date", flat=True).first()
        if d: dts.append(d)
        d = aum.values_list("date", flat=True).first()
        if d: dts.append(d)
        d = MetricEntry.objects.filter(customer=c, metric_id__in=lot_ids).values_list("date", flat=True).first() if lot_ids else None
        if d: dts.append(d)
        acct_date = max(dts) if dts else None

        if date_from and acct_date and str(acct_date) < date_from:
            continue
        if date_to and acct_date and str(acct_date) > date_to:
            continue

        rows.append({
            "customer_id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
            "country": c.country, "rm": getattr(c.assigned_to, "name", None),
            "date": acct_date.isoformat() if acct_date else None,
            "lots": round(float(lots), 2),
            "brokerage": round(float(rev["g"] or 0), 2),
            "commission": round(float(rev["cm"] or 0), 2),
            "net_revenue": round(float(rev["n"] or 0), 2),
            "deposits": round(float(dep), 2),
            "withdrawals": round(float(wd), 2),
            "net_aum": round(float(dep) - float(wd), 2),
            "insurance": round(float(con["i"] or 0), 2),
            "staking": round(float(con["s"] or 0), 2),
            "trading_loss": round(float(con["tl"] or 0), 2),
        })

    rows.sort(key=lambda r: r["lots"], reverse=True)
    keys = ["lots", "brokerage", "commission", "net_revenue", "deposits",
            "withdrawals", "net_aum", "trading_loss"]
    totals = {k: round(sum(r[k] for r in rows), 2) for k in keys}
    totals["traders"] = len(rows)
    return {"rows": rows, "totals": totals}


def fxartha_account_detail(customer):
    """Live read-through of one trader's FXArtha account — pulled straight from the
    API on every call. Balance, margin, live positions, orders, ledger and IB info
    are all real-time, so nothing is stored. `customer` is a CRM Customer instance.

    The API can't filter by user, so we page each feed and keep this trader's rows
    (positions/orders are tiny; ledger is capped to the 100 most-recent)."""
    from apps.integrations.models import IntegrationConnection
    from apps.integrations.services_fxartha import _Client, DEFAULT_BASE, DEFAULT_KEY

    uid = customer.external_id
    conn = IntegrationConnection.objects.filter(platform="fxartha").first()
    if not conn or not uid:
        return {"error": "Not a synced FXArtha trader."}
    base = (conn.config or {}).get("base_url") or DEFAULT_BASE
    key = (conn.config or {}).get("api_key") or DEFAULT_KEY
    cl = _Client(base, key)

    def mine(path):
        return [it for it in cl.paginate(path) if it.get("user_id") == uid]

    try:
        accounts = mine("/customers")
        positions = mine("/positions")
        orders = mine("/orders")
        ledger = mine("/ledger")
        ledger.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        ledger = ledger[:100]
        lead = next((l for l in cl.paginate("/leads") if l.get("user_id") == uid), {})
    except Exception as e:  # noqa: BLE001 — surface any upstream error to the UI
        return {"error": str(e)}

    def s(field):
        return round(sum(float(a.get(field) or 0) for a in accounts), 2)

    a0 = accounts[0] if accounts else {}
    account = {
        "name": a0.get("name") or customer.name,
        "email": a0.get("email") or customer.email,
        "country": a0.get("country") or customer.country,
        "broker": a0.get("broker"), "currency": a0.get("currency"),
        "account_type": a0.get("account_type"), "account_status": a0.get("account_status"),
        "kyc_status": a0.get("kyc_status"),
        "accounts": [a.get("account_number") for a in accounts],
        "leverage": a0.get("leverage"), "swap_free": a0.get("swap_free"),
        "minimum_deposit": a0.get("minimum_deposit"), "margin_level": a0.get("margin_level"),
        "balance": s("balance"), "equity": s("equity"), "credit": s("credit"),
        "margin_used": s("margin_used"), "free_margin": s("free_margin"),
        "current_pnl": s("current_pnl"), "realized_pnl": s("realized_pnl"),
        "net_pnl": s("net_pnl"), "total_profit": s("total_profit"),
        "total_deposit": s("total_deposit"), "total_withdrawal": s("total_withdrawal"),
        "lots_traded": s("lots_traded"), "gross_brokerage": s("gross_brokerage"),
    }
    ib = {k: lead.get(k) for k in (
        "is_ib", "ib_level", "ib_upline_email", "ib_pending_payout",
        "ib_custom_commission_per_lot", "ib_custom_commission_per_trade",
        "ib_commission_total", "referral_code", "referred_by",
        "referrals_count", "followers_count")}
    return {
        "customer_id": customer.id,
        "account": account,
        "positions": positions,
        "floating_pnl": round(sum(float(p.get("floating_pnl") or 0) for p in positions), 2),
        "orders": orders,
        "ledger": ledger,
        "ib": ib,
    }


def scoped_fxartha_traders(user, data):
    """Admins / Finance / HR see all; a manager sees only their subtree's traders."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(user, "role", None), "name", "")
    if is_admin_view(user) or role in ("Finance", "HR"):
        return data
    # scope by the trader's owning RM (customer.assigned_to) within the subtree
    from apps.crm.models import Customer
    keep_ids = set(subordinate_user_ids(user, include_self=True))
    allowed = set(Customer.objects.exclude(external_id="")
                  .filter(assigned_to_id__in=keep_ids).values_list("id", flat=True))
    rows = [r for r in data["rows"] if r["customer_id"] in allowed]
    keys = ["lots", "brokerage", "commission", "net_revenue", "deposits",
            "withdrawals", "net_aum", "trading_loss"]
    totals = {k: round(sum(r[k] for r in rows), 2) for k in keys}
    totals["traders"] = len(rows)
    return {"rows": rows, "totals": totals}
