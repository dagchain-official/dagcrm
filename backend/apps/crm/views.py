from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.scoping import BusinessScopedMixin
from apps.accounts.utils import is_admin_view

from .models import (
    Attachment, AumEntry, Business, Communication, ContributionEntry, ContributionWeight,
    Customer, CustomerProduct, Lead, LeadActivity, LeadInterest, LeadSource, MetricDefinition,
    MetricEntry, Opportunity, Product, Proposal, ProposalItem, Target, TargetAssignment,
)
from .serializers import (
    AttachmentSerializer, AumEntrySerializer, BusinessSerializer, CommunicationSerializer,
    ContributionEntrySerializer, ContributionWeightSerializer, CustomerProductSerializer,
    CustomerSerializer, LeadActivitySerializer, LeadInterestSerializer, LeadSerializer,
    LeadSourceSerializer, MetricDefinitionSerializer, MetricEntrySerializer, OpportunitySerializer,
    ProductSerializer, ProposalSerializer, TargetAssignmentSerializer, TargetSerializer,
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


class MetricDefinitionViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = MetricDefinition.objects.select_related("business", "product").all()
    serializer_class = MetricDefinitionSerializer
    filterset_fields = ["business", "product", "category", "source", "status"]
    search_fields = ["name"]


class MetricEntryViewSet(viewsets.ModelViewSet):
    queryset = (MetricEntry.objects
                .select_related("metric", "employee", "employee__user", "customer", "lead")
                .all())
    serializer_class = MetricEntrySerializer
    filterset_fields = ["metric", "employee", "date"]

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """For a DERIVED metric (e.g. Calls / Meetings / Leads Converted), auto-compute
        the value from the employee's real CRM activity for the month of the given date.
        Manual metrics return value=null (nothing to auto-fill)."""
        from django.utils import timezone
        from apps.hr.models import Employee

        md = MetricDefinition.objects.filter(id=request.query_params.get("metric")).first()
        emp = Employee.objects.filter(id=request.query_params.get("employee")).select_related("user").first()
        if not md or not emp or not emp.user_id or md.source != "derived" or not md.derived_key:
            return Response({"value": None, "derived": False})

        today = timezone.localdate()
        y, m = today.year, today.month
        ds = request.query_params.get("date")
        if ds:
            try:
                y, m = int(ds[:4]), int(ds[5:7])
            except (ValueError, IndexError):
                pass

        uid, key, val = emp.user_id, md.derived_key, 0
        if key in ("lead_activity:call", "lead_activity:meeting"):
            atype = key.split(":")[1]
            val = LeadActivity.objects.filter(user_id=uid, activity_type=atype,
                                              created_at__year=y, created_at__month=m).count()
        elif key == "lead:converted":
            qs = Lead.objects.filter(assigned_to_id=uid, status="converted")
            val = (qs.filter(converted_at__year=y, converted_at__month=m).count()
                   or qs.filter(converted_at__isnull=True).count())
        return Response({"value": val, "derived": True, "metric": md.name, "period": f"{m:02d}/{y}"})


class AumEntryViewSet(viewsets.ModelViewSet):
    queryset = AumEntry.objects.select_related("employee", "employee__user", "customer").all()
    serializer_class = AumEntrySerializer
    filterset_fields = ["employee", "customer", "entry_type", "date"]


class ContributionEntryViewSet(viewsets.ModelViewSet):
    queryset = (ContributionEntry.objects
                .select_related("employee", "employee__user", "customer", "business").all())
    serializer_class = ContributionEntrySerializer
    filterset_fields = ["employee", "customer", "business", "date"]


class ContributionWeightViewSet(viewsets.ModelViewSet):
    queryset = ContributionWeight.objects.all()
    serializer_class = ContributionWeightSerializer


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

    def _notify_assignee(self, lead, actor):
        """Tell an RM when a lead lands on them (skip self-assignment)."""
        if lead.assigned_to_id and lead.assigned_to_id != getattr(actor, "id", None):
            from apps.notifications.models import notify
            notify(lead.assigned_to, title="New lead assigned",
                   body=f"{lead.name} ({lead.lead_code}) was assigned to you.",
                   kind="info", link="/m/leads")

    def _enforce_assignment(self, serializer):
        """Non-assigners (e.g. Sales Executive) can't hand a lead to someone else —
        force it onto themselves regardless of what they sent."""
        from apps.accounts.access import can_assign_leads
        user = self.request.user
        if user.is_authenticated and not can_assign_leads(user):
            serializer.validated_data["assigned_to"] = user

    def perform_create(self, serializer):
        self._enforce_assignment(serializer)
        lead = serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)
        self._notify_assignee(lead, self.request.user)

    def perform_update(self, serializer):
        prev = self.get_object().assigned_to_id
        self._enforce_assignment(serializer)
        lead = serializer.save()
        if lead.assigned_to_id != prev:          # assignee changed -> notify the new one
            self._notify_assignee(lead, self.request.user)

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        """Lead 360 — profile + activity timeline + opportunities."""
        lead = self.get_object()
        acts = lead.activities.select_related("user").all()
        opps = lead.opportunities.select_related("product").all()
        return Response({
            "lead": LeadSerializer(lead, context={"request": request}).data,
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
            "lead": LeadSerializer(lead, context={"request": request}).data,
            "telephony": telephony,
        })

    @action(detail=False, methods=["post"])
    def distribute(self, request):
        """Auto-assign leads to RMs: round_robin | performance | manual."""
        from collections import defaultdict

        from django.contrib.auth import get_user_model

        from apps.accounts.access import can_assign_leads
        from apps.notifications.models import notify

        if not can_assign_leads(request.user):
            return Response({"detail": "You are not allowed to distribute leads."}, status=403)

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
            "origin_lead": LeadSerializer(lead, context={"request": request}).data if lead else None,
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


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.select_related("lead", "customer").prefetch_related("items").all()
    serializer_class = ProposalSerializer
    filterset_fields = ["status", "lead", "customer"]
    search_fields = ["title", "lead__name", "customer__name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def _actor(self, request):
        """Logged-in user, except the founder/superuser (whose actions aren't tracked)."""
        user = request.user if request.user.is_authenticated else None
        return None if (user and getattr(user, "is_superuser", False)) else user

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Mark a proposal as sent + log it on the lead's timeline (auto-advances status)."""
        from django.utils import timezone
        proposal = self.get_object()
        if proposal.status not in ("draft", "revised"):
            return Response({"detail": f"Cannot send a {proposal.status} proposal."}, status=400)
        proposal.status = "sent"
        proposal.sent_at = timezone.now()
        proposal.sent_by = self._actor(request)
        proposal.save(update_fields=["status", "sent_at", "sent_by"])
        if proposal.lead_id:
            LeadActivity.objects.create(
                lead=proposal.lead, user=self._actor(request), activity_type="proposal",
                remarks=f"Proposal {proposal.reference} sent: {proposal.title} (${proposal.total})",
            )
        return Response(self.get_serializer(proposal).data)

    @action(detail=True, methods=["post"])
    def send_via(self, request, pk=None):
        """Deliver the proposal to the client over WhatsApp or Email, log a
        Communication on the timeline, and mark the proposal as sent."""
        from django.utils import timezone
        from .models import Communication

        channel = (request.data.get("channel") or "").lower()
        if channel not in ("whatsapp", "email"):
            return Response({"detail": "channel must be 'whatsapp' or 'email'."}, status=400)

        p = self.get_object()
        target = p.lead or p.customer
        if not target:
            return Response({"detail": "Proposal has no lead/customer to send to."}, status=400)
        name = getattr(target, "name", "there")
        phone = getattr(target, "phone", "") or ""
        email = getattr(target, "email", "") or ""

        body = (f"Hi {name}, here is your proposal {p.reference}: {p.title}. "
                f"Total: ${p.total}.")
        if p.valid_until:
            body += f" Valid until {p.valid_until}."
        if p.notes:
            body += f"\nNote: {p.notes}"

        if channel == "whatsapp":
            if not phone:
                return Response({"detail": "No phone number on the recipient."}, status=400)
            from .telephony import send_whatsapp
            result = send_whatsapp(phone, body)
        else:
            if not email:
                return Response({"detail": "No email on the recipient."}, status=400)
            from django.conf import settings
            from django.core.mail import send_mail
            try:
                send_mail(f"Proposal {p.reference}: {p.title}", body,
                          settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                result = {"live": True, "note": "Email sent"}
            except Exception as e:  # noqa: BLE001
                result = {"live": False, "error": str(e)[:150]}

        Communication.objects.create(lead=p.lead, customer=p.customer, channel=channel,
                                     message=body, direction="outbound")

        if p.status in ("draft", "revised"):
            p.status = "sent"
            p.sent_at = timezone.now()
            p.sent_by = self._actor(request)
            p.save(update_fields=["status", "sent_at", "sent_by"])
            if p.lead_id:
                LeadActivity.objects.create(
                    lead=p.lead, user=self._actor(request), activity_type="proposal",
                    remarks=f"Proposal {p.reference} sent via {channel}: {p.title}")
        return Response({"channel": channel, **result, **self.get_serializer(p).data})

    @action(detail=True, methods=["post"])
    def revise(self, request, pk=None):
        """Create the next version of a proposal. The old version is frozen
        (is_current=False) so the full revision history is preserved."""
        old = self.get_object()
        siblings = Proposal.objects.filter(number=old.number) if old.number else Proposal.objects.filter(pk=old.pk)
        next_version = max((s.version for s in siblings), default=old.version) + 1

        new = Proposal.objects.create(
            number=old.number, version=next_version, parent=old, is_current=True,
            title=old.title, lead=old.lead, customer=old.customer, business=old.business,
            status="draft", valid_until=old.valid_until, notes=old.notes,
            tax_percent=old.tax_percent, created_by=self._actor(request),
        )
        for it in old.items.all():
            ProposalItem.objects.create(
                proposal=new, description=it.description, quantity=it.quantity,
                unit_price=it.unit_price, discount=it.discount,
            )
        new.recompute()
        # freeze every other version under this number
        siblings.exclude(pk=new.pk).update(is_current=False)
        return Response(self.get_serializer(new).data, status=201)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept a proposal and drive the full CRM flow:
        lead → customer (convert) → opportunity (won) → revenue → customer products."""
        from django.utils import timezone
        from apps.sales.models import Revenue

        p = self.get_object()
        if p.status == "accepted":
            return Response({"detail": "Proposal already accepted."}, status=400)

        p.status = "accepted"
        p.accepted_at = timezone.now()
        p.save(update_fields=["status", "accepted_at"])

        customer = p.customer
        # 1) Convert the lead into a customer if needed.
        if not customer and p.lead_id:
            lead = p.lead
            customer = Customer.objects.create(
                name=lead.name, email=lead.email, phone=lead.phone,
                country=lead.country, lead=lead,
            )
            if lead.status != "converted":
                lead.status = "converted"
                lead.save(update_fields=["status"])
            p.customer = customer
            p.save(update_fields=["customer"])

        # match proposal line items back to catalogue products (by name within the business)
        matched = []
        if p.business_id:
            for it in p.items.all():
                prod = Product.objects.filter(business_id=p.business_id, name=it.description).first()
                if prod:
                    matched.append(prod)

        # 2) Close-won opportunity off the lead.
        if p.lead_id:
            Opportunity.objects.create(
                lead=p.lead, product=matched[0] if matched else None,
                assigned_to=p.lead.assigned_to, stage="won",
                expected_revenue=p.total, status="closed",
            )

        # 3) Book revenue + attach products to the Customer 360 profile.
        if customer:
            for prod in matched:
                CustomerProduct.objects.get_or_create(
                    customer=customer, business_id=p.business_id, product=prod,
                    defaults={"status": "active"},
                )
            Revenue.objects.create(
                customer=customer, business_id=p.business_id,
                product=matched[0] if matched else None,
                gross_revenue=p.total, commission=0,
            )

        # 4) Timeline note for accountability.
        if p.lead_id:
            LeadActivity.objects.create(
                lead=p.lead, user=self._actor(request), activity_type="note",
                remarks=f"Proposal {p.reference} accepted (${p.total}) — converted to revenue.",
            )
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Mark a proposal as rejected (lost) and log it."""
        from django.utils import timezone
        p = self.get_object()
        p.status = "rejected"
        p.rejected_at = timezone.now()
        p.save(update_fields=["status", "rejected_at"])
        if p.lead_id:
            LeadActivity.objects.create(
                lead=p.lead, user=self._actor(request), activity_type="note",
                remarks=f"Proposal {p.reference} rejected by client.",
            )
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        import io

        from django.http import HttpResponse
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        p = self.get_object()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        brand = colors.HexColor("#4f46e5")
        biz = p.business.name if p.business_id else "DAGOS"

        # ---- branded header (per-business letterhead) ----
        c.setFillColor(brand)
        c.rect(0, h - 32 * mm, w, 32 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(20 * mm, h - 18 * mm, biz)
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 25 * mm, "Commercial Proposal")
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(w - 20 * mm, h - 15 * mm, p.number or "DRAFT")
        c.setFont("Helvetica", 10)
        c.drawRightString(w - 20 * mm, h - 21 * mm, f"Version {p.version}  ·  {p.status.upper()}")
        if p.valid_until:
            c.drawRightString(w - 20 * mm, h - 27 * mm, f"Valid until {p.valid_until}")

        y = h - 46 * mm
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 15)
        c.drawString(20 * mm, y, p.title)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#475569"))
        contact = (p.customer.name if p.customer_id else p.lead.name if p.lead_id else "—")
        c.drawString(20 * mm, y - 7 * mm, f"Prepared for: {contact}")
        if p.created_by_id:
            c.drawString(20 * mm, y - 12 * mm, f"Prepared by: {p.created_by.name}")

        # ---- items table (with discount column) ----
        ty = y - 24 * mm
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, ty, "Service / Product")
        c.drawRightString(w - 95 * mm, ty, "Qty")
        c.drawRightString(w - 70 * mm, ty, "Unit Price")
        c.drawRightString(w - 45 * mm, ty, "Disc %")
        c.drawRightString(w - 20 * mm, ty, "Amount")
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.line(20 * mm, ty - 2 * mm, w - 20 * mm, ty - 2 * mm)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#334155"))
        ry = ty - 9 * mm
        for it in p.items.all():
            c.drawString(20 * mm, ry, (it.description or "")[:46])
            c.drawRightString(w - 95 * mm, ry, f"{it.quantity:g}")
            c.drawRightString(w - 70 * mm, ry, f"${it.unit_price:,.2f}")
            c.drawRightString(w - 45 * mm, ry, f"{it.discount:g}%")
            c.drawRightString(w - 20 * mm, ry, f"${it.amount:,.2f}")
            ry -= 8 * mm

        # ---- totals breakdown ----
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.line(w - 80 * mm, ry - 1 * mm, w - 20 * mm, ry - 1 * mm)
        by = ry - 7 * mm
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#475569"))
        for label, val in [("Subtotal", p.subtotal), ("Discount", -p.discount_total),
                           (f"Tax ({p.tax_percent:g}%)", p.tax_amount)]:
            c.drawString(w - 80 * mm, by, label)
            c.drawRightString(w - 20 * mm, by, f"${val:,.2f}")
            by -= 6 * mm

        c.setFillColor(brand)
        c.roundRect(w - 80 * mm, by - 13 * mm, 60 * mm, 12 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(w - 76 * mm, by - 9 * mm, "TOTAL")
        c.drawRightString(w - 24 * mm, by - 9 * mm, f"${p.total:,.2f}")

        # ---- notes, terms & signature ----
        fy = by - 28 * mm
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 9)
        if p.notes:
            c.drawString(20 * mm, fy, f"Notes: {p.notes[:95]}")
            fy -= 6 * mm
        c.drawString(20 * mm, fy, "Terms: Prices in USD. This proposal is valid until the date above "
                                  "and subject to acceptance.")
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.line(20 * mm, 28 * mm, 80 * mm, 28 * mm)
        c.line(w - 80 * mm, 28 * mm, w - 20 * mm, 28 * mm)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, 24 * mm, "Authorised Signature")
        c.drawString(w - 80 * mm, 24 * mm, "Client Acceptance")
        c.drawCentredString(w / 2, 12 * mm, f"{biz} · Generated by DAGOS · {p.reference}")

        c.showPage()
        c.save()
        buf.seek(0)
        resp = HttpResponse(buf, content_type="application/pdf")
        fname = (p.number or f"proposal_{p.id}").replace(" ", "_")
        resp["Content-Disposition"] = f'attachment; filename="{fname}_v{p.version}.pdf"'
        return resp
