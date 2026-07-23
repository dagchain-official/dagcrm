"""Self-service helpers for real-time attendance + auto activity tracking."""
from django.utils import timezone

from .models import Attendance, Employee, EmployeeActivity, level_for_role


def ensure_employee(user):
    """Map a user to one Employee record. Super Admin is NOT an employee."""
    if not user or not user.is_authenticated or user.is_superuser:
        return None
    # tolerate (and self-heal) duplicate rows so .get_or_create can't blow up
    emps = list(Employee.objects.filter(user=user).order_by("id"))
    if emps:
        if len(emps) > 1:                       # keep the oldest, drop the rest
            Employee.objects.filter(id__in=[e.id for e in emps[1:]]).delete()
        return emps[0]
    role_name = getattr(user.role, "name", "")
    return Employee.objects.create(
        user=user, designation=role_name or "Staff",
        hierarchy_level=level_for_role(role_name),   # org level follows the role
    )


def today_attendance(user):
    emp = ensure_employee(user)
    if not emp:
        return None
    att, _ = Attendance.objects.get_or_create(
        employee=emp, date=timezone.localdate(), defaults={"status": "present"}
    )
    return att


def today_activity(user):
    emp = ensure_employee(user)
    if not emp:
        return None
    act, _ = EmployeeActivity.objects.get_or_create(employee=emp, date=timezone.localdate())
    return act


def bump_activity(user, field, n=1):
    """Auto-increment an activity counter from a real action (call/note/ticket)."""
    if not user or not user.is_authenticated or user.is_superuser:
        return
    act = today_activity(user)
    if not act:
        return
    setattr(act, field, getattr(act, field) + n)
    act.save(update_fields=[field])
