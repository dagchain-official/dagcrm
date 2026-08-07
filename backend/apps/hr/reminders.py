"""Daily HR reminder pass — the proactive "Automation/Notifications" layer for
the HR suite. One idempotent function scans for things due soon and pushes an
in-app notification. Safe to run several times a day: `notify_once` dedupes by
(user, title, link) within the same calendar day, so restarts / multiple 6h
ticks never double-send."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.notifications.models import Notification, notify

User = get_user_model()

# expiry / due-date thresholds (days out) at which we nudge — chosen so a rolling
# delta naturally fires once per threshold, no per-item state needed.
THRESHOLDS = {30, 14, 7, 3, 1, 0}
# HR Helpdesk SLA by priority (hours) — breach past this nudges HR daily.
SLA_HOURS = {"urgent": 4, "high": 8, "medium": 24, "low": 48}


def notify_once(user, title, body="", kind="info", link="", today=None):
    """notify() but at most one identical (title, link) per user per day."""
    if not user:
        return
    today = today or timezone.localdate()
    if Notification.objects.filter(user=user, title=title, link=link,
                                   created_at__date=today).exists():
        return
    notify(user, title=title, body=body, kind=kind, link=link)


def _hr_users():
    return list(User.objects.filter(role__name="HR", status="active"))


def run_hr_reminders(today=None):
    """Run every reminder rule once. Returns a small dict of counts (for tests)."""
    today = today or timezone.localdate()
    now = timezone.now()
    hr = _hr_users()
    counts = {"expiry": 0, "anniversary": 0, "pip": 0, "sla": 0, "training": 0,
              "missing_docs": 0, "monthly_reviews": 0}

    import calendar
    from .models import Appraisal, Employee, EmployeeDocument, PIP, TrainingAssignment
    try:
        from .models import HRTicket
    except Exception:  # noqa: BLE001
        HRTicket = None

    def recipients(emp):
        """Employee + their manager + all HR — the people who should act."""
        ppl = list(hr)
        if emp and emp.user_id:
            ppl.append(emp.user)
            if emp.manager_id:
                ppl.append(emp.manager)
        # de-dup by id
        seen, out = set(), []
        for u in ppl:
            if u and u.id not in seen:
                seen.add(u.id); out.append(u)
        return out

    # 1) Document expiry — passport / visa on the Employee + Document Vault rows
    def fire_expiry(emp, label, d):
        if not d:
            return
        delta = (d - today).days
        if delta not in THRESHOLDS:
            return
        when = "expires today" if delta == 0 else f"expires in {delta} day{'s' if delta != 1 else ''}"
        name = emp.user.name if emp.user_id else "An employee"
        for u in recipients(emp):
            notify_once(u, title=f"{label} {when}",
                        body=f"{name}'s {label} ({d:%d %b %Y}) {when}.",
                        kind="warning", link=f"/hr/employee/{emp.id}", today=today)
        counts["expiry"] += 1

    for emp in Employee.objects.select_related("user", "manager").exclude(user__is_superuser=True):
        fire_expiry(emp, "Passport", emp.passport_expiry)
        fire_expiry(emp, "Visa", emp.visa_expiry)
    for vd in EmployeeDocument.objects.select_related("employee__user", "employee__manager"):
        lbl = vd.get_doc_type_display() + (f" · {vd.title}" if vd.title else "")
        fire_expiry(vd.employee, lbl, vd.expiry_date)

    # 2) Work anniversary — nudge HR + manager (drives appraisal / increment)
    for emp in Employee.objects.select_related("user", "manager").exclude(user__is_superuser=True):
        j = emp.joining_date
        if not j or (j.month, j.day) != (today.month, today.day):
            continue
        years = today.year - j.year
        if years < 1:
            continue
        name = emp.user.name if emp.user_id else "An employee"
        for u in (hr + ([emp.manager] if emp.manager_id else [])):
            notify_once(u, title=f"{name} — {years}-year anniversary 🎉",
                        body=f"{name} completes {years} year{'s' if years != 1 else ''} today. Time for an appraisal review.",
                        kind="info", link=f"/hr/employee/{emp.id}", today=today)
        counts["anniversary"] += 1

    # 3) PIP review coming up
    for pip in PIP.objects.select_related("employee__user", "employee__manager", "owner").filter(status="active"):
        if not pip.end_date:
            continue
        delta = (pip.end_date - today).days
        if delta not in THRESHOLDS:
            continue
        name = pip.employee.user.name if pip.employee.user_id else "An employee"
        when = "due today" if delta == 0 else f"due in {delta} day{'s' if delta != 1 else ''}"
        targets = list(hr) + ([pip.owner] if pip.owner_id else [])
        if pip.employee.manager_id:
            targets.append(pip.employee.manager)
        for u in targets:
            notify_once(u, title=f"PIP review {when}: {name}",
                        body=f"{name}'s improvement-plan review is {when} ({pip.end_date:%d %b}).",
                        kind="warning", link="/m/pips", today=today)
        counts["pip"] += 1

    # 4) HR Helpdesk SLA breach — open ticket older than its priority SLA
    if HRTicket is not None:
        for t in HRTicket.objects.select_related("raised_by", "assigned_to").filter(status__in=["open", "in_progress"]):
            sla = SLA_HOURS.get(t.priority, 24)
            age_h = (now - t.created_at).total_seconds() / 3600
            if age_h < sla:
                continue
            targets = list(hr) + ([t.assigned_to] if t.assigned_to_id else [])
            for u in targets:
                notify_once(u, title=f"HR ticket SLA breached: {t.subject[:60]}",
                            body=f"Open {t.get_priority_display()} ticket from {t.raised_by.name} is past its {sla}h SLA.",
                            kind="error", link="/m/hr-tickets", today=today)
            counts["sla"] += 1

    # 5) Training due / overdue
    for ta in (TrainingAssignment.objects.select_related("employee__user", "module")
               .exclude(status__in=["completed", "exempted"])):
        if not ta.due_date:
            continue
        delta = (ta.due_date - today).days
        if delta not in THRESHOLDS and delta >= 0:
            continue
        emp = ta.employee
        title = ta.module.title if ta.module_id else "training"
        if delta < 0:
            head, kind = f"Training overdue: {title}", "error"
            body = f"'{title}' was due {-delta} day{'s' if -delta != 1 else ''} ago."
        else:
            when = "due today" if delta == 0 else f"due in {delta} day{'s' if delta != 1 else ''}"
            head, kind = f"Training {when}: {title}", "warning"
            body = f"'{title}' is {when} ({ta.due_date:%d %b})."
        if emp.user_id:
            notify_once(emp.user, title=head, body=body, kind=kind, link="/m/training-assignments", today=today)
        counts["training"] += 1

    # 6) Missing required documents — weekly nudge (Mondays) for each employee
    if today.weekday() == 0:
        REQUIRED = [("passport", "Passport"), ("visa", "Visa"), ("emirates_id", "Emirates / National ID")]
        have = set(EmployeeDocument.objects.values_list("employee_id", "doc_type"))
        for emp in Employee.objects.select_related("user", "manager").exclude(user__is_superuser=True):
            missing = [lbl for key, lbl in REQUIRED if (emp.id, key) not in have]
            if not missing:
                continue
            name = emp.user.name if emp.user_id else "An employee"
            body = "Missing: " + ", ".join(missing)
            for u in recipients(emp):
                notify_once(u, title=f"Documents incomplete: {name}", body=body,
                            kind="warning", link=f"/hr/employee/{emp.id}", today=today)
            counts["missing_docs"] += 1

    # 7) Monthly review — auto-create one appraisal record per employee per month
    period = f"{calendar.month_abbr[today.month]} {today.year}"
    for emp in Employee.objects.select_related("user", "manager").exclude(user__is_superuser=True):
        appr, made = Appraisal.objects.get_or_create(
            employee=emp, period=period, source="monthly",
            defaults={"status": "self"})
        if not made:
            continue
        name = emp.user.name if emp.user_id else "An employee"
        targets = list(hr) + ([emp.manager] if emp.manager_id else [])
        if emp.user_id:
            targets.append(emp.user)
        for u in targets:
            notify_once(u, title=f"Monthly review — {period}",
                        body=f"{name}'s monthly review record is ready for self-review, leader & HR.",
                        kind="info", link="/m/appraisals", today=today)
        counts["monthly_reviews"] += 1

    return counts
