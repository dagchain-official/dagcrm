"""Auto-advance a lead's status from engagement — driven first by the CALL
OUTCOME, then the MEETING status, then the plain activity type.

So a call that reaches "Interested" pushes the lead to Qualified; "Meeting
Booked" to Meeting Booked; "Not Interested" parks it in Nurture; "Converted"
closes it won — all without the RM touching the status field.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LeadActivity

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
