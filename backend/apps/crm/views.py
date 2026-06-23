from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.scoping import BusinessScopedMixin
from apps.accounts.utils import is_admin_view

from .models import (
    Attachment, Business, Communication, Customer, CustomerProduct, Lead, LeadActivity,
    LeadInterest, LeadSource, Opportunity, Product, Target, TargetAssignment,
)
from .serializers import (
    AttachmentSerializer, BusinessSerializer, CommunicationSerializer,
    CustomerProductSerializer, CustomerSerializer, LeadActivitySerializer,
    LeadInterestSerializer, LeadSerializer, LeadSourceSerializer, OpportunitySerializer,
    ProductSerializer, TargetAssignmentSerializer, TargetSerializer,
)


class BusinessViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    business_scope_field = "id"
    queryset = Business.objects.prefetch_related("products").all()
    serializer_class = BusinessSerializer
    search_fields = ["name"]


class ProductViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = Product.objects.select_related("business").all()
    serializer_class = ProductSerializer
    filterset_fields = ["business", "status"]
    search_fields = ["name"]


class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.all()
    serializer_class = LeadSourceSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related("source", "assigned_to").prefetch_related("interests").all().order_by("-created_at")
    serializer_class = LeadSerializer
    filterset_fields = ["status", "source", "assigned_to", "country"]
    search_fields = ["name", "email", "phone", "lead_code"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_admin_view(self.request.user):
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        """Lead 360 — profile + activity timeline + opportunities."""
        lead = self.get_object()
        acts = lead.activities.select_related("user").all()
        opps = lead.opportunities.select_related("product").all()
        return Response({
            "lead": LeadSerializer(lead).data,
            "activities": LeadActivitySerializer(acts, many=True).data,
            "opportunities": OpportunitySerializer(opps, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def engage(self, request, pk=None):
        """Call / WhatsApp / Email / Proposal — logs activity, auto-advances
        status (via signal), and triggers Twilio for call/whatsapp."""
        from .telephony import make_call, send_whatsapp

        lead = self.get_object()
        kind = request.data.get("type", "note")          # call|whatsapp|email|proposal|note
        remarks = request.data.get("remarks", "")
        message = request.data.get("message", "")
        user = request.user if request.user.is_authenticated else None
        if user and user.is_superuser:
            user = None  # founder's actions not tracked as activity

        labels = {"call": "Call placed", "whatsapp": "WhatsApp sent", "email": "Email sent",
                  "proposal": "Proposal sent", "meeting": "Meeting", "note": "Note"}
        activity = LeadActivity.objects.create(
            lead=lead, user=user, activity_type=kind,
            remarks=remarks or labels.get(kind, kind),
        )

        telephony = None
        if kind in ("whatsapp", "email", "proposal"):
            Communication.objects.create(
                lead=lead,
                channel="whatsapp" if kind == "whatsapp" else "email",
                direction="outbound",
                message=message or (f"{labels.get(kind)} to {lead.name}"),
            )
        if kind == "call":
            telephony = make_call(lead.phone, getattr(user, "phone", "") or None)
        elif kind == "whatsapp":
            telephony = send_whatsapp(lead.phone, message or f"Hi {lead.name}, following up.")

        lead.refresh_from_db()  # status may have auto-advanced via signal
        return Response({
            "activity": LeadActivitySerializer(activity).data,
            "lead": LeadSerializer(lead).data,
            "telephony": telephony,
        })

    @action(detail=False, methods=["post"])
    def distribute(self, request):
        """Auto-assign leads to RMs: round_robin | performance | manual."""
        from collections import defaultdict

        from django.contrib.auth import get_user_model

        from apps.notifications.models import notify

        User = get_user_model()
        strategy = request.data.get("strategy", "round_robin")
        lead_ids = request.data.get("lead_ids")
        target_user = request.data.get("user_id")

        leads = Lead.objects.all()
        leads = leads.filter(id__in=lead_ids) if lead_ids else leads.filter(assigned_to__isnull=True)
        leads = list(leads)
        if not leads:
            return Response({"assigned": 0, "detail": "No unassigned leads to distribute."})

        counts = defaultdict(int)
        rm_by_name = {}

        if strategy == "manual":
            u = User.objects.filter(id=target_user).first()
            if not u:
                return Response({"detail": "Select a valid user."}, status=400)
            for l in leads:
                l.assigned_to = u
            counts[u.name] = len(leads)
            rm_by_name[u.name] = u
        else:
            from apps.accounts.access import ASSIGNABLE_LEAD_ROLES
            rms = list(User.objects.filter(
                role__name__in=ASSIGNABLE_LEAD_ROLES, is_active=True))
            if not rms:
                return Response({"detail": "No sales reps available to assign."}, status=400)

            if strategy == "performance":
                # top performers (higher conversion rate) get proportionally more
                weighted = []
                for rm in rms:
                    total = Lead.objects.filter(assigned_to=rm).count()
                    conv = Lead.objects.filter(assigned_to=rm, status="converted").count()
                    rate = (conv / total) if total else 0
                    weighted += [rm] * (1 + round(rate * 4))  # 1..5 slots
                for i, l in enumerate(leads):
                    rm = weighted[i % len(weighted)]
                    l.assigned_to = rm
                    counts[rm.name] += 1
                    rm_by_name[rm.name] = rm
            else:  # round_robin — load-balanced (fewest current leads first)
                load = {rm.id: Lead.objects.filter(assigned_to=rm).count() for rm in rms}
                for l in leads:
                    rm = min(rms, key=lambda r: load[r.id])
                    l.assigned_to = rm
                    load[rm.id] += 1
                    counts[rm.name] += 1
                    rm_by_name[rm.name] = rm

        Lead.objects.bulk_update(leads, ["assigned_to"])
        for name, c in counts.items():
            notify(rm_by_name[name], title="New leads assigned",
                   body=f"{c} new lead{'s' if c != 1 else ''} were assigned to you.",
                   kind="info", link="/m/leads")

        return Response({"assigned": len(leads), "strategy": strategy, "breakdown": dict(counts)})

    @action(detail=False, methods=["get"])
    def import_template(self, request):
        from django.http import HttpResponse
        content = ("name,email,phone,country,source,status\n"
                   "John Doe,john@example.com,+919999999999,India,Website,new\n"
                   "Jane Smith,jane@example.com,+447700900000,UK,Referral,contacted\n")
        resp = HttpResponse(content, content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="leads_template.csv"'
        return resp

    @action(detail=False, methods=["post"])
    def import_csv(self, request):
        """Bulk-import leads from an uploaded CSV file."""
        import csv
        import io

        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "No file uploaded."}, status=400)
        try:
            text = f.read().decode("utf-8-sig")
        except Exception:
            return Response({"detail": "Could not read file. Use a UTF-8 CSV."}, status=400)

        reader = csv.DictReader(io.StringIO(text))
        valid_status = {"new", "contacted", "qualified", "converted", "lost"}
        existing_codes = set(Lead.objects.values_list("lead_code", flat=True))
        existing_phones = set(Lead.objects.exclude(phone="").values_list("phone", flat=True))
        existing_emails = set(Lead.objects.exclude(email="").values_list("email", flat=True))
        source_cache = {}
        counter = [1]

        def gen_code():
            while True:
                code = f"IMP{counter[0]:05d}"
                counter[0] += 1
                if code not in existing_codes:
                    existing_codes.add(code)
                    return code

        created, skipped, errors = 0, 0, []
        user = request.user if request.user.is_authenticated else None
        for idx, row in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            name = row.get("name")
            if not name:
                errors.append({"row": idx, "reason": "Missing name"})
                continue
            phone, email = row.get("phone", ""), row.get("email", "")
            if phone and phone in existing_phones:
                skipped += 1
                continue
            if email and email in existing_emails:
                skipped += 1
                continue
            source = None
            sname = row.get("source")
            if sname:
                if sname not in source_cache:
                    source_cache[sname] = LeadSource.objects.get_or_create(name=sname)[0]
                source = source_cache[sname]
            st = row.get("status", "new").lower()
            code = row.get("lead_code") or gen_code()
            if code in existing_codes and not row.get("lead_code"):
                code = gen_code()
            try:
                Lead.objects.create(
                    lead_code=code, name=name, email=email, phone=phone,
                    country=row.get("country", ""), source=source,
                    status=st if st in valid_status else "new",
                    assigned_to=user, created_by=user,
                )
                created += 1
                existing_codes.add(code)
                if phone:
                    existing_phones.add(phone)
                if email:
                    existing_emails.add(email)
            except Exception as e:
                errors.append({"row": idx, "reason": str(e)[:80]})

        return Response({
            "created": created, "skipped": skipped,
            "errors": errors[:25], "total_errors": len(errors),
        })


class LeadInterestViewSet(viewsets.ModelViewSet):
    queryset = LeadInterest.objects.select_related("business", "product").all()
    serializer_class = LeadInterestSerializer
    filterset_fields = ["lead", "business", "product"]


class LeadActivityViewSet(viewsets.ModelViewSet):
    queryset = LeadActivity.objects.select_related("user").all()
    serializer_class = LeadActivitySerializer
    filterset_fields = ["lead", "user", "activity_type"]

    def get_queryset(self):
        # Super Admin's activity is never shown to anyone
        qs = super().get_queryset().exclude(user__is_superuser=True)
        if not is_admin_view(self.request.user):
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if user and user.is_superuser:
            user = None  # founder's actions are not tracked as activity
        obj = serializer.save(user=user)
        # Auto activity tracking: real call/note actions bump the counters.
        if user:
            from apps.hr.services import bump_activity
            if obj.activity_type == "call":
                bump_activity(user, "calls_completed")
            elif obj.activity_type == "note":
                bump_activity(user, "notes_added")


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.select_related("lead", "product", "assigned_to").all()
    serializer_class = OpportunitySerializer
    filterset_fields = ["stage", "status", "assigned_to", "product"]
    search_fields = ["lead__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_admin_view(self.request.user):
            qs = qs.filter(assigned_to=self.request.user)
        return qs


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.prefetch_related("products").all().order_by("-created_at")
    serializer_class = CustomerSerializer
    filterset_fields = ["country"]
    search_fields = ["name", "email", "phone"]

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        """Customer 360 — everything about one customer in one payload."""
        from apps.sales.models import Revenue
        from apps.sales.serializers import RevenueSerializer
        from apps.support.models import Ticket
        from apps.support.serializers import TicketSerializer

        customer = self.get_object()
        revenues = Revenue.objects.filter(customer=customer).select_related("business", "product")
        tickets = Ticket.objects.filter(customer=customer).select_related("assigned_to")
        comms = customer.communications.all()
        products = customer.products.select_related("business", "product")
        lead = customer.lead

        total_net = revenues.aggregate(s=Sum("net_revenue"))["s"] or 0
        total_gross = revenues.aggregate(s=Sum("gross_revenue"))["s"] or 0
        open_tickets = tickets.exclude(status__in=["resolved", "closed"]).count()

        # unified timeline (newest first)
        timeline = []
        for r in revenues:
            timeline.append({"type": "revenue", "date": r.created_at,
                             "title": f"Revenue · {r.business.name if r.business else ''}",
                             "detail": f"Net ${r.net_revenue}", "icon": "dollar"})
        for t in tickets:
            timeline.append({"type": "ticket", "date": t.created_at,
                             "title": f"Ticket {t.ticket_no}",
                             "detail": f"{t.category or ''} · {t.status}", "icon": "ticket"})
        for c in comms:
            timeline.append({"type": "communication", "date": c.created_at,
                             "title": f"{c.channel.title()} · {c.direction}",
                             "detail": (c.message or "")[:80], "icon": "message"})
        if lead:
            for a in lead.activities.all():
                timeline.append({"type": "activity", "date": a.created_at,
                                 "title": f"{a.activity_type.title()} (as lead)",
                                 "detail": a.remarks or a.next_action or "", "icon": "activity"})
        timeline.sort(key=lambda e: e["date"], reverse=True)

        return Response({
            "customer": CustomerSerializer(customer).data,
            "kpis": {
                "total_net_revenue": total_net,
                "total_gross_revenue": total_gross,
                "products_count": products.count(),
                "open_tickets": open_tickets,
                "total_tickets": tickets.count(),
                "communications_count": comms.count(),
            },
            "products": CustomerProductSerializer(products, many=True).data,
            "revenues": RevenueSerializer(revenues, many=True).data,
            "tickets": TicketSerializer(tickets, many=True).data,
            "communications": CommunicationSerializer(comms, many=True).data,
            "origin_lead": LeadSerializer(lead).data if lead else None,
            "attachments": AttachmentSerializer(customer.attachments.all(), many=True, context={"request": request}).data,
            "timeline": timeline,
        })


class CustomerProductViewSet(viewsets.ModelViewSet):
    queryset = CustomerProduct.objects.select_related("business", "product").all()
    serializer_class = CustomerProductSerializer
    filterset_fields = ["customer", "business", "product", "status"]


class CommunicationViewSet(viewsets.ModelViewSet):
    queryset = Communication.objects.all()
    serializer_class = CommunicationSerializer
    filterset_fields = ["lead", "customer", "channel", "direction"]


class TargetViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = Target.objects.select_related("business").prefetch_related("assignments").all()
    serializer_class = TargetSerializer
    filterset_fields = ["target_type", "business"]


class TargetAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TargetAssignment.objects.select_related("user", "team", "department").all()
    serializer_class = TargetAssignmentSerializer
    filterset_fields = ["target", "user", "team", "department"]


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related("uploaded_by").all()
    serializer_class = AttachmentSerializer
    filterset_fields = ["customer", "ticket"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user if self.request.user.is_authenticated else None)
