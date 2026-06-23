from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .fxartha import fx_get, is_configured


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fx_status(request):
    return Response({"configured": is_configured(),
                     "base_url": settings.FXARTHA_API_URL or ""})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fx_dashboard(request):
    data, code = fx_get("/dashboard")
    return Response(data, status=code)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fx_leads(request):
    params = {k: request.GET.get(k) for k in
              ["page", "per_page", "search", "date_from", "date_to"]}
    data, code = fx_get("/leads", params)
    return Response(data, status=code)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fx_customers(request):
    params = {k: request.GET.get(k) for k in ["page", "per_page", "search"]}
    data, code = fx_get("/customers", params)
    return Response(data, status=code)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fx_import_leads(request):
    """Pull a page of FX Artha leads into the CRM Lead table (dedup + source tag)."""
    from apps.crm.models import Lead, LeadSource

    data, code = fx_get("/leads", {
        "page": request.data.get("page", 1),
        "per_page": request.data.get("per_page", 100),
        "search": request.data.get("search", ""),
    })
    if code != 200:
        return Response(data, status=code)

    items = data.get("items", data if isinstance(data, list) else [])
    src, _ = LeadSource.objects.get_or_create(name="FX Artha")
    existing_phones = set(Lead.objects.exclude(phone="").values_list("phone", flat=True))
    existing_emails = set(Lead.objects.exclude(email="").values_list("email", flat=True))
    existing_codes = set(Lead.objects.values_list("lead_code", flat=True))
    counter = [Lead.objects.filter(lead_code__startswith="FXA").count() + 1]

    def code_gen():
        while True:
            c = f"FXA{counter[0]:05d}"
            counter[0] += 1
            if c not in existing_codes:
                existing_codes.add(c)
                return c

    created = skipped = 0
    user = request.user if request.user.is_authenticated else None
    for it in items:
        phone = str(it.get("phone") or "").strip()
        email = str(it.get("email") or "").strip()
        if (phone and phone in existing_phones) or (email and email in existing_emails):
            skipped += 1
            continue
        Lead.objects.create(
            lead_code=code_gen(), name=it.get("name") or "FX Artha Lead",
            email=email, phone=phone, country=it.get("country", "") or "",
            source=src, status="new", created_by=user,
        )
        created += 1
        if phone:
            existing_phones.add(phone)
        if email:
            existing_emails.add(email)

    return Response({"created": created, "skipped": skipped, "received": len(items)})
