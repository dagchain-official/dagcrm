"""Auto-advance a lead's status from engagement — driven first by the CALL
OUTCOME, then the MEETING status, then the plain activity type.

So a call that reaches "Interested" pushes the lead to Qualified; "Meeting
Booked" to Meeting Booked; "Not Interested" parks it in Nurture; "Converted"
closes it won — all without the RM touching the status field.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Lead, LeadActivity, Opportunity

# once a lead is Qualified it becomes a deal (Opportunity) and leaves the leads
# list; these lead statuses map to the open opportunity's stage.
OPP_OPEN_STAGES = {
    "qualified": "active", "meeting_booked": "active",
    "meeting_done": "active", "negotiation": "negotiation",
}

# funnel order (bigger = further along)
RANK = {
    "new": 0, "assigned": 1, "attempted": 2, "contacted": 3, "qualified": 4,
    "meeting_booked": 5, "meeting_done": 6, "negotiation": 7, "converted": 8,
}

# a plain activity type nudges the lead this far
ADVANCE = {
    "call": "contacted", "outbound_call": "contacted", "inbound_call": "contacted",
    "callback": "contacted", "whatsapp": "contacted", "email": "contacted",
    "meeting": "meeting_done", "note": None, "followup": None,
    "document_collection": None, "service_call": None,
}
# a call outcome that moves the lead FORWARD (only if it's ahead of now)
OUTCOME_ADVANCE = {
    "no_answer": "attempted", "busy": "attempted", "voicemail": "attempted",
    "connected": "contacted", "callback": "contacted", "interested": "qualified",
    "meeting_booked": "meeting_booked",
}
# a call outcome that SETS the status outright (a decision, not a step)
OUTCOME_SET = {"not_interested": "nurture", "wrong_number": "lost", "converted": "converted"}
# a meeting status → where the lead should sit
MEETING_ADVANCE = {"scheduled": "meeting_booked", "confirmed": "meeting_booked",
                   "completed": "meeting_done"}


def advance_lead_status(lead, activity):
    if not lead or lead.status in ("converted", "lost"):
        return  # terminal — never override a closed lead

    outcome = getattr(activity, "outcome", "") or ""
    if outcome in OUTCOME_SET:
        lead.status = OUTCOME_SET[outcome]
        lead.save(update_fields=["status"])
        return

    target = (OUTCOME_ADVANCE.get(outcome)
              or MEETING_ADVANCE.get(getattr(activity, "meeting_status", "") or "")
              or ADVANCE.get(activity.activity_type))
    if target and RANK.get(target, 0) > RANK.get(lead.status, 0):
        lead.status = target
        lead.save(update_fields=["status"])


@receiver(post_save, sender=LeadActivity)
def on_activity(sender, instance, created, **kwargs):
    if created:
        advance_lead_status(instance.lead, instance)


def sync_opportunity(lead):
    """Keep the deal pipeline in step with the lead's status (CRM-own leads only):
      Qualified … Negotiation  -> an OPEN Opportunity (lead has left the leads list)
      Converted                -> that Opportunity is Won + closed (moves to Customers)
      Lost                     -> that Opportunity is Lost + closed
    """
    opp = lead.opportunities.order_by("-id").first()
    st = lead.status
    if st in OPP_OPEN_STAGES:
        if opp is None:
            Opportunity.objects.create(
                lead=lead, assigned_to=lead.assigned_to,
                stage=OPP_OPEN_STAGES[st], status="open",
                expected_revenue=lead.expected_value or 0)
        elif opp.status == "open":
            opp.stage = OPP_OPEN_STAGES[st]
            opp.assigned_to = lead.assigned_to
            if not opp.expected_revenue and lead.expected_value:
                opp.expected_revenue = lead.expected_value
            opp.save(update_fields=["stage", "assigned_to", "expected_revenue"])
    elif st in ("converted", "lost") and opp and opp.status == "open":
        opp.stage = "won" if st == "converted" else "lost"
        opp.status = "closed"
        opp.save(update_fields=["stage", "status"])


@receiver(post_save, sender=Lead)
def on_lead_saved(sender, instance, **kwargs):
    """Pipeline movement: Qualified -> Opportunity, Converted -> Customer (+ won),
    Lost -> lost. The Customer link also pulls in the person's live FX Artha /
    DAGChain account if one exists, so real purchases/revenue surface and keep
    updating via sync."""
    if instance.external_id == "":       # CRM-own leads only (synced leads have their own flow)
        sync_opportunity(instance)
    if instance.status == "converted":
        from .linking import ensure_customer_for_lead, ensure_postsale_for_lead
        customer = ensure_customer_for_lead(instance)
        ensure_postsale_for_lead(instance, customer)
