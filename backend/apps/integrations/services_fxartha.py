"""FXArtha poll connector — pulls the platform's read-only CRM API into ours.

  /dashboard  -> snapshot stored on the connection
  /leads      -> upsert Lead      (keyed by external_id = user_id)
  /customers  -> upsert Customer  (+ Revenue + AUM deposit/withdrawal)

All writes are idempotent (update_or_create on external_id) so re-syncing every
few minutes never duplicates. assigned_rm is always null upstream, so leads are
auto-assigned CRM-side and AUM/revenue attribute through that RM.
"""
import requests
from django.db import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

DEFAULT_BASE = "https://api.fxartha.com/api/v1/crm"
DEFAULT_KEY = "crm_test_key_123"


class _Client:
    def __init__(self, base, key):
        self.base = base.rstrip("/")
        self.key = key

    def get(self, path, params=None):
        r = requests.get(f"{self.base}{path}", params=params,
                         headers={"X-API-Key": self.key}, timeout=25)
        if r.status_code == 401:
            raise RuntimeError("Invalid API key (401).")
        if r.status_code == 503:
            raise RuntimeError("FXArtha CRM API not configured (503).")
        r.raise_for_status()
        return r.json()

    def paginate(self, path, per_page=100):
        page = 1
        while True:
            data = self.get(path, {"page": page, "per_page": per_page})
            items = data.get("items", [])
            for it in items:
                yield it
            total = data.get("total", 0)
            if page * per_page >= total or not items:
                break
            page += 1


def _date(iso):
    dt = parse_datetime(iso) if iso else None
    return (dt or timezone.now()).date()


def _upsert_lead(conn, item, source, next_rm):
    from apps.crm.models import Lead
    uid = item["user_id"]
    contact = {
        "name": item.get("name") or "Unknown",
        "email": item.get("email") or "",
        "phone": item.get("phone") or "",
        "country": item.get("country") or "",
    }
    lead = Lead.objects.filter(external_id=uid).first()
    if lead:                                   # update contact only — don't clobber CRM-side status/RM
        for k, v in contact.items():
            setattr(lead, k, v)
        lead.save()
        return lead, False

    assigned = next_rm() if conn.auto_assign else None
    n = Lead.objects.filter(lead_code__startswith="FXA").count() + 1
    # retry on collision — two overlapping syncs can pick the same code
    for _ in range(20):
        while Lead.objects.filter(lead_code=f"FXA{n:05d}").exists():
            n += 1
        try:
            lead = Lead.objects.create(
                external_id=uid, lead_code=f"FXA{n:05d}", source=source,
                status="converted" if item.get("has_account") else "new",
                assigned_to=assigned, **contact)
            break
        except IntegrityError:
            n += 1
    else:
        return None, False
    if assigned:
        from apps.notifications.models import notify
        notify(assigned, title="New FXArtha lead", body=f"{contact['name']} imported from FXArtha",
               kind="info", link="/m/leads")
    return lead, True


def _sync_customer(conn, item, business, tx_map=None, trade_map=None,
                   lots_metric=None, trades_metric=None):
    from apps.crm.models import (AumEntry, ContributionEntry, Customer, Lead,
                                 MetricDefinition, MetricEntry)
    from apps.hr.models import Employee
    from apps.sales.models import Revenue

    uid = item["user_id"]
    acct = item.get("account_number") or uid
    lead = Lead.objects.filter(external_id=uid).first()

    fields = {
        "name": item.get("name") or "Unknown",
        "email": item.get("email") or "",
        "phone": item.get("phone") or "",
        "country": item.get("country") or "",
        "lead": lead,
    }
    cust, _ = Customer.objects.update_or_create(external_id=uid, defaults=fields)
    # Seed the owner from the lead's RM on first sight; never overwrite a manual
    # reassignment (that's why assigned_to is not in `defaults`).
    if cust.assigned_to_id is None and lead and lead.assigned_to_id:
        cust.assigned_to_id = lead.assigned_to_id
        cust.save(update_fields=["assigned_to"])

    # Revenue (skip empty). net_revenue is auto (gross − commission).
    gross = float(item.get("gross_brokerage") or 0)
    comm = float(item.get("ib_commission") or 0)
    if gross or comm:
        Revenue.objects.update_or_create(
            external_id=f"fxa:{acct}",
            defaults={"customer": cust, "business": business,
                      "gross_revenue": gross, "commission": comm})

    # Everything below is attributed to the customer's current owner (a manual
    # reassignment wins over the lead's original RM).
    owner_uid = cust.assigned_to_id or (lead.assigned_to_id if lead else None)
    emp = Employee.objects.filter(user_id=owner_uid).first() if owner_uid else None
    when = _date(item.get("account_opened_at"))
    # Deposits/withdrawals are per-USER in /transactions (the /customers rows report
    # them as 0). A trader can hold several accounts (several /customers rows), so
    # these — and lots — are keyed by user_id with the rolled-up per-user figure;
    # re-running per account-row just rewrites the same row (no double-counting).
    # Fall back to the per-account customer field only if the tx feed was absent.
    _txu = (tx_map or {}).get(uid)
    if _txu is not None:
        dep = float(_txu.get("deposit") or 0)
        wd = float(_txu.get("withdrawal") or 0)
    else:
        dep = float(item.get("total_deposit") or 0)
        wd = float(item.get("total_withdrawal") or 0)
    dep_acct = float(item.get("total_deposit") or 0)  # per-account (for contribution)

    # AUM (PART 11) — deposits / withdrawals -> Net New AUM (per trader)
    if emp and dep:
        AumEntry.objects.update_or_create(
            external_id=f"fxa-dep:{uid}",
            defaults={"employee": emp, "customer": cust, "business": business,
                      "entry_type": "deposit", "amount": dep, "date": when, "note": "FXArtha sync"})
    if emp and wd:
        AumEntry.objects.update_or_create(
            external_id=f"fxa-wd:{uid}",
            defaults={"employee": emp, "customer": cust, "business": business,
                      "entry_type": "withdrawal", "amount": wd, "date": when, "note": "FXArtha sync"})

    # Contribution (PART 12) — per-account components (brokerage/loss are per account)
    brokerage = float(item.get("brokerage") or item.get("gross_brokerage") or 0)
    insurance = float(item.get("insurance") or 0)
    staking = float(item.get("staking") or 0)
    trading_loss = float(item.get("trading_loss") or 0)
    if emp and (brokerage or insurance or staking or trading_loss or dep_acct):
        ContributionEntry.objects.update_or_create(
            external_id=f"fxa-contrib:{acct}",
            defaults={"employee": emp, "customer": cust, "business": business,
                      "deposit": dep_acct, "trading_loss": trading_loss, "brokerage": brokerage,
                      "insurance": insurance, "staking": staking, "other": 0, "date": when})

    # KPI (PART 10) — per-trader figures, keyed by user_id.
    # Lots + trade count: the /trades aggregate is per user (see _aggregate_trades);
    # fall back to the per-customer fields when the trades feed is absent.
    _tr = (trade_map or {}).get(uid)
    if _tr is not None:
        lots = float(_tr.get("lots") or 0)
        trades = int(_tr.get("count") or 0)
    else:
        lots = float(item.get("lots_traded") or 0)
        trades = int(item.get("trades_count") or 0)
    if emp and lots:
        md = lots_metric or MetricDefinition.objects.filter(name__icontains="lot").first()
        if md:
            MetricEntry.objects.update_or_create(
                external_id=f"fxa-lots:{uid}",
                defaults={"metric": md, "employee": emp, "customer": cust,
                          "value": lots, "date": when, "note": "FXArtha sync"})
    # Trades Taken KPI — total number of trades the trader placed (count)
    if emp and trades and trades_metric:
        MetricEntry.objects.update_or_create(
            external_id=f"fxa-trades:{uid}",
            defaults={"metric": trades_metric, "employee": emp, "customer": cust,
                      "value": trades, "date": when, "note": "FXArtha sync"})
    # New Deposits KPI — the trader's deposit total
    if emp and dep:
        mdd = MetricDefinition.objects.filter(name__icontains="deposit").first()
        if mdd:
            MetricEntry.objects.update_or_create(
                external_id=f"fxa-newdep:{uid}",
                defaults={"metric": mdd, "employee": emp, "customer": cust,
                          "value": dep, "date": when, "note": "FXArtha sync"})
    # Active Traders KPI — one per synced trader (per user_id)
    if emp:
        mda = MetricDefinition.objects.filter(name__icontains="active").first()
        if mda:
            if mda.aggregation != "count":     # ensure it totals a head-count
                mda.aggregation = "count"
                mda.save(update_fields=["aggregation"])
            MetricEntry.objects.update_or_create(
                external_id=f"fxa-active:{uid}",
                defaults={"metric": mda, "employee": emp, "customer": cust,
                          "value": 1, "date": when, "note": "FXArtha sync"})
    return cust


def _aggregate_transactions(client):
    """Roll up /transactions into {user_id: {deposit, withdrawal}} — SETTLED only.
    Deposits/withdrawals are not on the /customers rows — they live here. Only
    APPROVED transactions are counted: a pending deposit isn't real money yet, so
    totalling it as AUM/deposits would overstate the figure (FXArtha confirmed the
    pending deposits should NOT be included)."""
    skip = {"pending", "rejected", "failed", "cancelled", "canceled", "declined",
            "processing", "on_hold", "unconfirmed"}
    out = {}
    try:
        for t in client.paginate("/transactions"):
            uid = t.get("user_id")
            if not uid or str(t.get("status") or "approved").lower() in skip:
                continue
            ty = (t.get("type") or "").lower()
            if ty not in ("deposit", "withdrawal"):
                continue
            row = out.setdefault(uid, {"deposit": 0.0, "withdrawal": 0.0})
            row[ty] += float(t.get("amount") or 0)
    except (RuntimeError, requests.RequestException):
        pass  # endpoint optional — fall back to per-customer fields
    return out


def _aggregate_trades(client):
    """Roll up /trades into {user_id: {"lots": total_lots, "count": n_trades}}.
    `count` is how many trades the trader placed; `lots` their summed volume."""
    out = {}
    try:
        for tr in client.paginate("/trades"):
            uid = tr.get("user_id")
            if uid:
                row = out.setdefault(uid, {"lots": 0.0, "count": 0})
                row["lots"] += float(tr.get("lots") or 0)
                row["count"] += 1
    except (RuntimeError, requests.RequestException):
        pass
    return out


def sync_fxartha(conn):
    from apps.crm.models import Business, Lead, LeadSource
    from .models import IntegrationLog
    from .services import _next_rm

    base = (conn.config or {}).get("base_url") or DEFAULT_BASE
    key = (conn.config or {}).get("api_key") or DEFAULT_KEY
    client = _Client(base, key)

    try:
        dashboard = client.get("/dashboard")
        source, _ = LeadSource.objects.get_or_create(name="FXArtha")
        business, _ = Business.objects.get_or_create(name="FX Artha")

        # Ensure the "Lots Traded" KPI exists so per-trade lots can be recorded.
        from apps.crm.models import MetricDefinition
        lots_metric, _ = MetricDefinition.objects.get_or_create(
            name="Lots Traded",
            defaults={"unit": "lots", "aggregation": "sum",
                      "category": "activity", "source": "manual"})
        # "Trades Taken" KPI — per-trader count of trades placed.
        trades_metric, _ = MetricDefinition.objects.get_or_create(
            name="Trades Taken",
            defaults={"unit": "count", "aggregation": "sum",
                      "category": "activity", "source": "manual"})

        # Deposits/withdrawals live in /transactions and per-trade lots in /trades
        # (the /customers rows report 0 deposits). Roll both up per user_id.
        tx_map = _aggregate_transactions(client)
        trade_map = _aggregate_trades(client)

        lead_created = lead_updated = 0
        for item in client.paginate("/leads"):
            _, created = _upsert_lead(conn, item, source, _next_rm)
            lead_created += int(created)
            lead_updated += int(not created)

        cust_synced = 0
        synced_uids = set()
        for item in client.paginate("/customers"):
            _sync_customer(conn, item, business, tx_map, trade_map,
                           lots_metric, trades_metric)
            synced_uids.add(item.get("user_id"))
            cust_synced += 1

        # Sync EVERY transacting/trading user — not just those the /customers feed
        # exposes. FXArtha's /customers feed returns only a subset, so deposits,
        # withdrawals, lots and trades for users that appear only in /transactions
        # or /trades were being dropped (the platform deposit total never
        # reconciled). Materialise a customer for each remaining user from their
        # already-synced lead so their figures roll up too. Idempotent
        # (update_or_create on external_id), so re-syncing never duplicates.
        extra_synced = extra_unowned = 0
        for uid in (set(tx_map) | set(trade_map)) - synced_uids:
            if not uid:
                continue
            lead = Lead.objects.filter(external_id=uid).first()
            syn = {"user_id": uid}
            if lead:
                syn.update(name=lead.name, email=lead.email,
                           phone=lead.phone, country=lead.country)
            cust = _sync_customer(conn, syn, business, tx_map, trade_map,
                                  lots_metric, trades_metric)
            extra_synced += 1
            # Deposits need an owning RM (AumEntry.employee is non-null). Count any
            # user we still couldn't attribute so nothing is silently lost.
            if cust and not (cust.assigned_to_id or (lead and lead.assigned_to_id)):
                extra_unowned += 1
        cust_synced += extra_synced
    except (RuntimeError, requests.RequestException) as e:
        IntegrationLog.objects.create(connection=conn, status="error", message=str(e)[:300])
        return {"error": str(e)}

    conn.status = "connected"
    conn.config = {**(conn.config or {}), "dashboard": dashboard,
                   "last_sync": timezone.now().isoformat()}
    conn.total_leads = lead_created + lead_updated
    conn.last_lead_at = timezone.now()
    conn.save()

    summary = {"leads_created": lead_created, "leads_updated": lead_updated,
               "customers_synced": cust_synced, "extra_users_synced": extra_synced,
               "unowned_users": extra_unowned, "dashboard": dashboard}
    msg = (f"{lead_created} new + {lead_updated} updated leads, {cust_synced} customers "
           f"({extra_synced} beyond the /customers feed)")
    if extra_unowned:
        msg += f"; {extra_unowned} users had no RM — their deposits could not be attributed"
    IntegrationLog.objects.create(connection=conn, status="success", message=msg)
    return summary
