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


def _next_rm():
    """Pick the Sales Executive / Team Leader with the fewest leads (load-balanced)."""
    from django.contrib.auth import get_user_model
    from apps.crm.models import Lead
    User = get_user_model()
    rms = list(User.objects.filter(role__name__in=["Sales Executive", "Team Leader"], is_active=True))
    if not rms:
        return None
    return min(rms, key=lambda u: Lead.objects.filter(assigned_to=u).count())


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

    assigned = _next_rm() if conn.auto_assign else None
    lead = Lead.objects.create(
        lead_code=f"{prefix}{n:05d}", name=name, email=email, phone=phone,
        country=fields.get("country", ""), source=source, status="new",
        assigned_to=assigned,
    )

    # notify the RM
    if assigned:
        from apps.notifications.models import notify
        notify(assigned, title="New lead assigned",
               body=f"{name} via {conn.label}", kind="info", link="/m/leads")
    return lead, True


def process_webhook(conn, payload):
    """Normalize → ingest each → update stats + log. Returns summary dict."""
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
