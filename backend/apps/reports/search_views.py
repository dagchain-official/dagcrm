from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.crm.models import Customer, Lead
from apps.support.models import Ticket


@api_view(["GET"])
def global_search(request):
    """Global search across leads, customers, and tickets."""
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return Response({"results": []})

    results = []
    for l in Lead.objects.pipeline().filter(
        Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q) | Q(lead_code__icontains=q)
    )[:5]:
        results.append({"type": "Lead", "id": l.id, "title": f"{l.lead_code} · {l.name}",
                        "subtitle": l.phone or l.email or "", "link": "/m/leads"})

    for c in Customer.objects.filter(
        Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
    )[:5]:
        results.append({"type": "Customer", "id": c.id, "title": c.name,
                        "subtitle": c.email or c.phone or "", "link": f"/customers/{c.id}"})

    for t in Ticket.objects.filter(
        Q(ticket_no__icontains=q) | Q(category__icontains=q) | Q(customer__name__icontains=q)
    ).select_related("customer")[:5]:
        results.append({"type": "Ticket", "id": t.id, "title": f"{t.ticket_no} · {t.category or ''}",
                        "subtitle": t.customer.name if t.customer else t.status, "link": "/m/tickets"})

    return Response({"results": results})
