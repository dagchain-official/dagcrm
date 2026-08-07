"""Unified lead-ingestion pipeline shared by every platform webhook."""
from django.utils import timezone


def normalize(platform, payload):
    """Turn a platform's raw webhook payload into a list of normalized leads.

    Handles the common shapes: Meta (entry/field_data), Google (user_column_data),
    a generic {leads:[...]} batch, or a single flat {name,email,phone} object.
    """
    out = []

    def _flat(d):
        g = lambda *keys: next((str(d[k]).strip() for k in keys if d.get(k)), "")
        return {
            "name": g("name", "full_name", "full name", "fullName"),
            "email": g("email", "email_address", "e-mail"),
            "phone": g("phone", "phone_number", "phone number", "mobile"),
            "country": g("country", "country_code"),
            "campaign": g("campaign", "campaign_name", "ad_name"),
        }

    # Meta Lead Ads format
    if isinstance(payload, dict) and "entry" in payload:
        for entry in payload.get("entry", []):
            for ch in entry.get("changes", []):
                fd = ch.get("value", {}).get("field_data", [])
                rec = {f.get("name"): (f.get("values") or [""])[0] for f in fd}
                out.append(_flat(rec))
        if out:
            return out

    # Google Ads lead form format
    if isinstance(payload, dict) and "user_column_data" in payload:
        rec = {c.get("column_id", "").lower(): c.get("string_value", "")
               for c in payload.get("user_column_data", [])}
        rec["campaign"] = payload.get("campaign_id", "")
        return [_flat(rec)]

    # Generic batch
    if isinstance(payload, dict) and isinstance(payload.get("leads"), list):
        return [_flat(x) for x in payload["leads"]]
    if isinstance(payload, list):
        return [_flat(x) for x in payload]

    # Single flat lead
    if isinstance(payload, dict):
        return [_flat(payload)]
    return out


def fetch_meta_lead(conn, leadgen_id):
    """Meta's leadgen webhook carries only a leadgen_id — pull the real answers
    from the Graph API using the page access token stored on the connection."""
    token = (conn.config or {}).get("access_token")
    if not token:
        return {}
    try:
        import requests
        r = requests.get(
            f"https://graph.facebook.com/v19.0/{leadgen_id}",
            params={"access_token": token,
                    "fields": "field_data,campaign_name,ad_name,created_time"},
            timeout=15,
        )
        return r.json() if r.ok else {}
    except Exception:  # noqa: BLE001 — never break ingestion on a fetch error
        return {}


def expand_meta(conn, payload):
    """In-place: for any Meta change that has only a leadgen_id, fetch its
    field_data so the shared normalize() can read name/email/phone as usual."""
    if not isinstance(payload, dict):
        return payload
    for entry in payload.get("entry", []):
        for ch in entry.get("changes", []):
            val = ch.get("value", {})
            if not val.get("field_data") and val.get("leadgen_id"):
                data = fetch_meta_lead(conn, val["leadgen_id"])
                if data.get("field_data"):
                    val["field_data"] = data["field_data"]
                    if data.get("campaign_name") or data.get("ad_name"):
                        val["field_data"].append(
                            {"name": "campaign", "values": [data.get("campaign_name") or data.get("ad_name")]})
    return payload


def _next_rm(business=None):
    """Least-busy CLOCKED-IN front-line agent — anything auto-assigned (CRM leads
    AND synced FX Artha traders) goes only to an active RM. None if nobody is
    clocked in, so the record stays unassigned until an RM marks attendance."""
    from apps.crm.assignment import next_active_agent
    return next_active_agent()


def ingest_lead(conn, fields):
    """Create one Lead from normalized fields. Returns (lead, created_bool)."""
    from apps.crm.models import Lead, LeadSource

    name = fields.get("name") or "Unknown Lead"
    phone = fields.get("phone", "")
    email = fields.get("email", "")

    # dedup by phone/email
    if phone and Lead.objects.filter(phone=phone).exists():
        return None, False
    if email and Lead.objects.filter(email=email).exists():
        return None, False

    source, _ = LeadSource.objects.get_or_create(name=conn.source_name)
    # unique lead code
    prefix = conn.platform[:3].upper()
    n = Lead.objects.filter(lead_code__startswith=prefix).count() + 1
    while Lead.objects.filter(lead_code=f"{prefix}{n:05d}").exists():
        n += 1

    assigned = _next_rm(conn.business) if conn.auto_assign else None
    lead = Lead.objects.create(
        lead_code=f"{prefix}{n:05d}", name=name, email=email, phone=phone,
        country=fields.get("country", ""), source=source, status="new",
        business=conn.business, assigned_to=assigned,
    )

    # notify the RM
    if assigned:
        from apps.notifications.models import notify
        notify(assigned, title="New lead assigned",
               body=f"{name} via {conn.label}", kind="info", link="/m/leads")
    return lead, True


def process_webhook(conn, payload):
    """Normalize → ingest each → update stats + log. Returns summary dict."""
    if conn.platform == "meta":
        payload = expand_meta(conn, payload)   # leadgen_id → real field_data
    leads = normalize(conn.platform, payload)
    created = skipped = 0
    for f in leads:
        _, was = ingest_lead(conn, f)
        created += was
        skipped += (not was)

    if created:
        conn.total_leads += created
        conn.last_lead_at = timezone.now()
        conn.save(update_fields=["total_leads", "last_lead_at"])

    from .models import IntegrationLog
    IntegrationLog.objects.create(
        connection=conn, status="success" if created else "skipped",
        message=f"{created} created, {skipped} skipped (received {len(leads)})",
    )
    return {"received": len(leads), "created": created, "skipped": skipped}
