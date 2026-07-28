"""Front-line lead-assignment rules — active-only routing, the 5-minute
reassignment sweep, and the sequential (work-oldest-first) lock.

All three apply ONLY to the front-line sales role ("Sales Executive", i.e. the
Relationship Manager / agent). Team Leaders, Sales Managers and above are never
auto-assigned leads, never reassigned away, and never locked.
"""
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

FRONTLINE_ROLE = "Sales Executive"       # the RM / agent role these rules govern
REASSIGN_MINUTES = 5


def is_frontline(user):
    """True for a Sales Executive (RM / agent) — the only role the rules govern."""
    role = getattr(user, "role", None)
    return bool(user and getattr(user, "is_authenticated", True) and role and role.name == FRONTLINE_ROLE)


def active_agent_ids():
    """Front-line agents who are clocked in RIGHT NOW (checked in today and not
    yet checked out) — the only people eligible to receive a lead."""
    from apps.hr.models import Attendance
    today = timezone.localdate()
    att = (Attendance.objects
           .filter(date=today, checkin__isnull=False, checkout__isnull=True,
                   status__in=["present", "half_day"])
           .select_related("employee__user__role"))
    ids = set()
    for a in att:
        u = a.employee.user if a.employee_id else None
        if u and u.is_active and not u.is_superuser and is_frontline(u):
            ids.add(u.id)
    return ids


def next_active_agent(exclude_id=None):
    """The least-busy clocked-in front-line agent (round-robin), or None if
    nobody is active. Optionally exclude one agent (the one we're moving off)."""
    from django.contrib.auth import get_user_model
    from .models import Lead
    ids = active_agent_ids()
    if exclude_id:
        ids = ids - {exclude_id}
    if not ids:
        return None
    users = list(get_user_model().objects.filter(id__in=ids))
    # fewest OPEN leads wins the next one
    return min(users, key=lambda u: Lead.objects.pipeline().filter(
        assigned_to=u, status__in=["new", "assigned"]).count())


def unlocked_lead_id(user):
    """The one lead a front-line agent may currently open — their OLDEST
    un-actioned lead. Every newer un-actioned lead stays locked until this one
    gets an activity. None if they have no un-actioned leads."""
    from .models import Lead
    if not is_frontline(user):
        return None
    return (Lead.objects.pipeline()
            .filter(assigned_to=user, status__in=["new", "assigned"])
            .annotate(n=Count("activities")).filter(n=0)
            .order_by("assigned_at", "created_at")
            .values_list("id", flat=True).first())


def reassign_stale_leads(minutes=REASSIGN_MINUTES):
    """Move any lead that has sat un-actioned on a front-line agent for longer
    than `minutes` to the next active agent, and hand unassigned new leads to an
    active agent too. Returns how many were moved. Safe to call on a timer."""
    from apps.notifications.models import notify
    from .models import Lead
    cutoff = timezone.now() - timedelta(minutes=minutes)
    moved = 0

    stale = (Lead.objects.pipeline().filter(status__in=["new", "assigned"])
             .annotate(n=Count("activities")).filter(n=0))

    # a) assigned but un-actioned past the SLA — only off a front-line agent
    for lead in stale.filter(assigned_to__isnull=False, assigned_at__lt=cutoff).select_related("assigned_to__role"):
        if not is_frontline(lead.assigned_to):
            continue
        nxt = next_active_agent(exclude_id=lead.assigned_to_id)
        if not nxt:
            continue                      # nobody else active — leave it put
        lead.assigned_to = nxt
        lead.save(update_fields=["assigned_to"])     # save() re-stamps assigned_at
        notify(nxt, title="Lead reassigned to you",
               body=f"{lead.name} ({lead.lead_code}) — the previous agent didn't act within {minutes} min.",
               kind="info", link="/m/leads")
        moved += 1

    # b) unassigned new leads — give them to whoever is active
    for lead in stale.filter(assigned_to__isnull=True):
        nxt = next_active_agent()
        if not nxt:
            break                         # nobody active — nothing to assign to
        lead.assigned_to = nxt
        lead.save(update_fields=["assigned_to"])
        notify(nxt, title="New lead assigned",
               body=f"{lead.name} ({lead.lead_code}) was assigned to you.",
               kind="info", link="/m/leads")
        moved += 1

    return moved
