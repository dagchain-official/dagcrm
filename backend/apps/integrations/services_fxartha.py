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


def _sync_customer(conn, item, business):
    from apps.crm.models import AumEntry, Customer, Lead
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

    # Revenue (skip empty). net_revenue is auto (gross − commission).
    gross = float(item.get("gross_brokerage") or 0)
    comm = float(item.get("ib_commission") or 0)
    if gross or comm:
        Revenue.objects.update_or_create(
            external_id=f"fxa:{acct}",
            defaults={"customer": cust, "business": business,
                      "gross_revenue": gross, "commission": comm})

    # AUM — attribute to the lead's auto-assigned RM's employee (if any)
    emp = None
    if lead and lead.assigned_to_id:
        emp = Employee.objects.filter(user_id=lead.assigned_to_id).first()
    dep = float(item.get("total_deposit") or 0)
    wd = float(item.get("total_withdrawal") or 0)
    if emp and (dep or wd):
        when = _date(item.get("account_opened_at"))
        if dep:
            AumEntry.objects.update_or_create(
                external_id=f"fxa-dep:{acct}",
                defaults={"employee": emp, "customer": cust, "entry_type": "deposit",
                          "amount": dep, "date": when, "note": "FXArtha sync"})
        if wd:
            AumEntry.objects.update_or_create(
                external_id=f"fxa-wd:{acct}",
                defaults={"employee": emp, "customer": cust, "entry_type": "withdrawal",
                          "amount": wd, "date": when, "note": "FXArtha sync"})
    return cust


def sync_fxartha(conn):
    from apps.crm.models import Business, LeadSource
    from .models import IntegrationLog
    from .services import _next_rm

    base = (conn.config or {}).get("base_url") or DEFAULT_BASE
    key = (conn.config or {}).get("api_key") or DEFAULT_KEY
    client = _Client(base, key)

    try:
        dashboard = client.get("/dashboard")
        source, _ = LeadSource.objects.get_or_create(name="FXArtha")
        business, _ = Business.objects.get_or_create(name="FX Artha")

        lead_created = lead_updated = 0
        for item in client.paginate("/leads"):
            _, created = _upsert_lead(conn, item, source, _next_rm)
            lead_created += int(created)
            lead_updated += int(not created)

        cust_synced = 0
        for item in client.paginate("/customers"):
            _sync_customer(conn, item, business)
            cust_synced += 1
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
               "customers_synced": cust_synced, "dashboard": dashboard}
    IntegrationLog.objects.create(
        connection=conn, status="success",
        message=f"{lead_created} new + {lead_updated} updated leads, {cust_synced} customers")
    return summary
