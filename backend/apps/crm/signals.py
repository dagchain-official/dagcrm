"""Auto-advance a lead's status as engagement activities happen."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LeadActivity

# how far each status is in the funnel
RANK = {"new": 0, "contacted": 1, "qualified": 2, "converted": 3, "lost": 3}
# which status an activity type pushes the lead toward
ADVANCE = {
    "call": "contacted",
    "whatsapp": "contacted",
    "email": "contacted",
    "meeting": "qualified",
    "proposal": "qualified",
    "note": None,
}


def advance_lead_status(lead, activity_type):
    target = ADVANCE.get(activity_type)
    if not target or not lead:
        return
    if lead.status in ("converted", "lost"):
        return  # terminal — don't override
    if RANK.get(target, 0) > RANK.get(lead.status, 0):
        lead.status = target
        lead.save(update_fields=["status"])


@receiver(post_save, sender=LeadActivity)
def on_activity(sender, instance, created, **kwargs):
    if created:
        advance_lead_status(instance.lead, instance.activity_type)
