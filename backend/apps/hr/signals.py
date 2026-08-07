"""Auto-timeline — key events in other HR modules drop a durable row into the
Employee Timeline (EmployeeEvent) so the history builds itself. All writes are
get_or_create on a deterministic (employee, kind, title) key, so repeated saves
never duplicate an event."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Appraisal, Employee, EmployeeEvent, EmployeeExit, PIP, Recognition


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
