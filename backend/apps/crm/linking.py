"""Identity-match a converted lead to their live platform account.

When a lead is Closed Won we check whether that same person already exists as a
synced FX Artha trader or DAGChain user (matched on email). If so, the lead IS
that account: we attach the lead to it and hand the
account to the lead's RM, so the person's real purchases and revenue — which the
integrations already sync every few minutes — start showing on the customer and
crediting the RM. Every future purchase keeps flowing in through the same sync;
nothing here has to run again.
"""
def platform_of(customer):
    """Which platform a synced customer belongs to (for labels/badges)."""
    if not customer or not customer.external_id:
        return ""
    # DagChainProfile is a OneToOne (related_name="dagchain"); its presence is
    # the reliable DAGChain marker. Everything else synced is an FX Artha trader.
    return "DAGChain" if hasattr(customer, "dagchain") else "FX Artha"


def find_platform_twin(email, phone=None):
    """A synced platform account with the same email as this lead, or None.
    Email only — unique enough to auto-link (phone is ignored)."""
    from .models import Customer

    email = (email or "").strip().lower()
    if not email:
        return None
    # match on email only (per request)
    return Customer.objects.exclude(external_id="").filter(email__iexact=email).first()


def ensure_customer_for_lead(lead):
    """Guarantee a Closed-Won lead has a Customer; link the platform twin if any.

    Idempotent — safe to call on every save of a converted lead.
    Returns the Customer (existing twin, or a freshly created CRM customer).
    """
    from .models import Customer, LeadActivity

    if lead.customers.exists():
        return lead.customers.first()

    twin = find_platform_twin(lead.email, lead.phone)
    if twin:
        changed = []
        if twin.lead_id != lead.id:
            twin.lead = lead
            changed.append("lead")
        # The RM who worked the lead now owns the account — revenue follows owner.
        if lead.assigned_to_id and twin.assigned_to_id != lead.assigned_to_id:
            twin.assigned_to = lead.assigned_to
            changed.append("assigned_to")
        if changed:
            twin.save(update_fields=changed)
        LeadActivity.objects.create(
            lead=lead, user=lead.assigned_to, activity_type="note",
            remarks=f"Converted — matched to existing {platform_of(twin)} account "
                    f"“{twin.name}”. Their purchases & revenue now show on this customer.",
        )
        return twin

    return Customer.objects.create(
        name=lead.name, email=lead.email, phone=lead.phone,
        country=lead.country, lead=lead, assigned_to=lead.assigned_to,
    )


def ensure_postsale_for_lead(lead, customer):
    """Seed a PostSale for a Closed-Won lead so its onboarding/service lifecycle can
    be tracked from the customer's record. The agent completes the rest. Idempotent
    — one seeded sale per lead."""
    from django.utils import timezone
    from .models import PostSale

    if not customer or PostSale.objects.filter(lead=lead).exists():
        return None
    biz = lead.business
    prod = None
    interest = lead.interests.first()
    if interest:
        biz = biz or interest.business
        prod = interest.product
    return PostSale.objects.create(
        customer=customer, lead=lead, agent=lead.assigned_to, business=biz, product=prod,
        close_date=timezone.now().date(), sale_type="new", sale_status="closed_won",
        gross_value=lead.expected_value or 0,
    )


def _merge_customer(loser, keeper):
    """Move a placeholder customer's records onto the real (platform) one, delete it."""
    from apps.sales.models import Revenue
    from apps.support.models import Ticket
    from .models import (Attachment, AumEntry, Communication, ContributionEntry,
                         CustomerProduct, MetricEntry, PostSale)
    if loser.id == keeper.id:
        return
    for Model in (Revenue, PostSale, CustomerProduct, Communication, AumEntry,
                  ContributionEntry, MetricEntry, Attachment, Ticket):
        Model.objects.filter(customer=loser).update(customer=keeper)
    loser.delete()


def link_pending_conversions():
    """Catch converted customers who open an FX Artha / DAGChain account AFTER
    converting: on each sync, re-match the still-unlinked ones by email/phone and
    attach the platform account (with its purchases & revenue) to the lead's RM.
    Returns how many were newly linked.

    ponytail: re-scans all CRM-own converted leads each sync; add a 'checked' flag
    on Lead if this ever gets slow.
    """
    from .models import Lead
    linked = 0
    for lead in (Lead.objects.pipeline().filter(status="converted")
                 .prefetch_related("customers")):
        custs = list(lead.customers.all())
        # skip if already on a platform account, or no placeholder customer exists
        if not custs or any(c.external_id for c in custs):
            continue
        twin = find_platform_twin(lead.email, lead.phone)
        if not twin or twin.lead_id:          # no match, or already linked elsewhere
            continue
        twin.lead = lead
        if lead.assigned_to_id:
            twin.assigned_to = lead.assigned_to
        twin.save(update_fields=["lead", "assigned_to"])
        for c in custs:                       # fold the placeholder(s) into the twin
            _merge_customer(c, twin)
        linked += 1
    return linked
