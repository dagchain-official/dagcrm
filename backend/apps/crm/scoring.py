"""Lead scoring — the same heuristic the AI service uses, computed in-process so
a lead's score always reflects its current source, contact info, engagement and
stage. Applied automatically on create/update and whenever an activity is logged.
"""

HOT_SOURCES = {"referral", "website", "whatsapp"}
WARM_SOURCES = {"meta ads", "google ads", "telegram", "facebook", "instagram", "linkedin", "tiktok"}

STATUS_BOOST = {"qualified": 15, "contacted": 8, "converted": 25, "lost": -25}


def compute_score(lead) -> int:
    """0-100 lead score. Base 30, plus source quality, contact info, engagement
    (activity count) and stage."""
    score = 30

    src = (lead.source.name.lower() if lead.source_id and lead.source else "")
    if src in HOT_SOURCES:
        score += 25
    elif src in WARM_SOURCES:
        score += 12

    if lead.email:
        score += 8
    if lead.phone:
        score += 10

    # engagement — number of logged activities (calls, meetings, notes…)
    activity_count = lead.activities.count() if lead.pk else 0
    if activity_count >= 3:
        score += 20
    elif activity_count >= 1:
        score += 10

    score += STATUS_BOOST.get(lead.status, 0)
    return max(0, min(100, score))


def rescore(lead):
    """Recompute and persist a lead's score (no-op if unchanged)."""
    new = compute_score(lead)
    if new != lead.score:
        lead.score = new
        lead.save(update_fields=["score"])
    return new
