"""Identity-match a converted lead to their live platform account.

When a lead is Closed Won we check whether that same person already exists as a
synced FX Artha trader or DAGChain user (matched on email, or a full phone
number). If so, the lead IS that account: we attach the lead to it and hand the
account to the lead's RM, so the person's real purchases and revenue — which the
integrations already sync every few minutes — start showing on the customer and
crediting the RM. Every future purchase keeps flowing in through the same sync;
nothing here has to run again.
"""
import re


def _digits(s):
    return re.sub(r"\D", "", s or "")


def platform_of(customer):
    """Which platform a synced customer belongs to (for labels/badges)."""
    if not customer or not customer.external_id:
        return ""
    # DagChainProfile is a OneToOne (related_name="dagchain"); its presence is
    # the reliable DAGChain marker. Everything else synced is an FX Artha trader.
    return "DAGChain" if hasattr(customer, "dagchain") else "FX Artha"


def find_platform_twin(email, phone):
    """A synced platform account that is the same person as this lead, or None.

    Email is the primary key (unique enough to auto-link). Phone is a fallback,
    but only for a real number — DAGChain stores just a dial code in `phone`, so
    we require >= 8 digits and compare the last 10 to avoid dial-code collisions.
    """
    from .models import Customer

    email = (email or "").strip().lower()
    digits = _digits(phone)
    phone10 = digits[-10:] if len(digits) >= 8 else ""

    synced = Customer.objects.exclude(external_id="")
    if email:
        hit = synced.filter(email__iexact=email).first()
        if hit:
            return hit
    if phone10:
        for c in synced.exclude(phone="").only("id", "phone"):
            if _digits(c.phone)[-10:] == phone10:
                return c
    return None


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
