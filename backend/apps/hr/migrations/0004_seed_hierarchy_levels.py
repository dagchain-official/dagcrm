# Seed default org hierarchy levels and map existing employees onto them
# (derived from each user's RBAC role — a one-time backfill, idempotent).
from django.db import migrations

# role name -> (level_name, level_order). Roles stay the source of truth for
# permissions; this only seeds the *org* dimension so rollups have a structure.
ROLE_TO_LEVEL = {
    "Business Head": ("Business Head", 1),
    "Sales Manager": ("Sales Manager", 2),
    "Team Leader": ("Team Leader", 3),
    "Sales Executive": ("Relationship Manager", 4),
}


def seed(apps, schema_editor):
    HierarchyLevel = apps.get_model("hr", "HierarchyLevel")
    Employee = apps.get_model("hr", "Employee")

    levels = {}
    for name, order in {v for v in ROLE_TO_LEVEL.values()}:
        lvl, _ = HierarchyLevel.objects.get_or_create(
            level_name=name, defaults={"level_order": order, "status": "active"})
        levels[name] = lvl

    for emp in Employee.objects.select_related("user", "user__role").all():
        if emp.hierarchy_level_id:
            continue
        role = getattr(getattr(emp.user, "role", None), "name", None)
        mapped = ROLE_TO_LEVEL.get(role)
        if mapped:
            emp.hierarchy_level = levels.get(mapped[0])
            emp.save(update_fields=["hierarchy_level"])


def unseed(apps, schema_editor):
    # detach employees, keep the (admin-editable) levels in place
    Employee = apps.get_model("hr", "Employee")
    Employee.objects.update(hierarchy_level=None)


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0003_hierarchylevel_employee_hierarchy_level'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
