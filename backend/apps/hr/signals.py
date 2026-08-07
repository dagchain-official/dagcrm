"""Auto-timeline — key events in other HR modules drop a durable row into the
Employee Timeline (EmployeeEvent) so the history builds itself. All writes are
get_or_create on a deterministic (employee, kind, title) key, so repeated saves
never duplicate an event."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.notifications.models import notify
from .models import (Appraisal, Assessment, Employee, EmployeeEvent, EmployeeExit,
                     PIP, Recognition)


def _add(employee, kind, title, details="", when=None):
    if not employee_id_ok(employee):
        return
    EmployeeEvent.objects.get_or_create(
        employee=employee, kind=kind, title=title[:200],
        defaults={"date": when or timezone.localdate(), "details": details[:2000]})


def employee_id_ok(emp):
    return bool(emp and getattr(emp, "id", None))


@receiver(post_save, sender=Employee)
def _on_employee(sender, instance, created, **kwargs):
    if created:
        _add(instance, "join", "Joined the company", when=instance.joining_date)


@receiver(post_save, sender=PIP)
def _on_pip(sender, instance, created, **kwargs):
    if created:
        _add(instance.employee, "pip", f"PIP started — {instance.reason[:80]}",
             details=instance.goals or "", when=instance.start_date)


@receiver(post_save, sender=Appraisal)
def _on_appraisal(sender, instance, **kwargs):
    if instance.status == "approved":
        _add(instance.employee, "appraisal", f"Appraisal approved — {instance.period}",
             details=f"Rating {instance.manager_rating}/5, increment {instance.increment_pct}%")
        if instance.promotion_to:
            _add(instance.employee, "promotion", f"Promoted to {instance.promotion_to}",
                 details=f"Appraisal {instance.period}")


@receiver(post_save, sender=Recognition)
def _on_recognition(sender, instance, **kwargs):
    if instance.status == "approved":
        _add(instance.employee, "recognition",
             f"{instance.get_award_display()} — {instance.reason[:60]}",
             details=instance.reason)


@receiver(post_save, sender=EmployeeExit)
def _on_exit(sender, instance, created, **kwargs):
    if created:
        _add(instance.employee, "exit", "Exit initiated",
             details=instance.reason or "", when=instance.resignation_date)


@receiver(post_save, sender=Assessment)
def _on_assessment(sender, instance, created, **kwargs):
    """Step 1 — a passed training activates the employee's login 'workspace'
    and pings HR with an onboarding notification."""
    if instance.result != "pass":
        return
    emp = instance.employee
    module = instance.module.title if instance.module_id else "training"
    _add(emp, "training", f"Passed: {module}")
    if not created:
        return
    if emp and emp.user_id and emp.user.status != "active":
        emp.user.status = "active"                 # provision the workspace
        emp.user.save(update_fields=["status"])
    U = get_user_model()
    who = emp.user.name if (emp and emp.user_id) else "An employee"
    for hr in U.objects.filter(role__name="HR", status="active"):
        notify(hr, title="Onboarding training passed",
               body=f"{who} passed {module} — account activated.",
               kind="success", link=f"/hr/employee/{emp.id}")
