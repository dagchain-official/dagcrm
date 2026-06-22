"""Self-service helpers for real-time attendance + auto activity tracking."""
from django.utils import timezone

from .models import Attendance, Employee, EmployeeActivity


def ensure_employee(user):
    """Every user maps to one Employee record (auto-created on first use)."""
    emp, _ = Employee.objects.get_or_create(
        user=user, defaults={"designation": getattr(user.role, "name", "") or "Staff"}
    )
    return emp


def today_attendance(user):
    emp = ensure_employee(user)
    att, _ = Attendance.objects.get_or_create(
        employee=emp, date=timezone.localdate(), defaults={"status": "present"}
    )
    return att


def today_activity(user):
    emp = ensure_employee(user)
    act, _ = EmployeeActivity.objects.get_or_create(employee=emp, date=timezone.localdate())
    return act


def bump_activity(user, field, n=1):
    """Auto-increment an activity counter from a real action (call/note/ticket)."""
    if not user or not user.is_authenticated:
        return
    act = today_activity(user)
    setattr(act, field, getattr(act, field) + n)
    act.save(update_fields=[field])
