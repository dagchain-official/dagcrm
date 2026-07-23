# The org level is now DERIVED from the RBAC role (it was dropped from the
# employee form). Make sure every role in the ladder has its level row with the
# right order, then put existing employees on the level their role implies.
from django.db import migrations

# kept in step with apps.accounts.access.ROLE_TO_LEVEL
ROLE_TO_LEVEL = {
    "Super Admin":     ("Business Head", 1),
    "Business Head":   ("Business Head", 1),
    "Sales Director":  ("Sales Director", 2),
    "Sales Manager":   ("Sales Manager", 3),
    "Team Leader":     ("Team Leader", 4),
    "Sales Executive": ("Relationship Manager", 5),
    "Support":         ("Support", 6),
    "HR":              ("HR", 6),
    "Finance":         ("Finance", 6),
}


def seed(apps, schema_editor):
    HierarchyLevel = apps.get_model("hr", "HierarchyLevel")
    Employee = apps.get_model("hr", "Employee")

    levels = {}
    for name, order in set(ROLE_TO_LEVEL.values()):
        lvl = HierarchyLevel.objects.filter(level_name=name).first()
        if lvl is None:
            lvl = HierarchyLevel.objects.create(level_name=name, level_order=order,
                                                status="active")
        elif lvl.level_order != order:
            # normalise the ladder so "manager sits above" comparisons hold
            lvl.level_order = order
            lvl.save(update_fields=["level_order"])
        levels[name] = lvl

    for emp in Employee.objects.select_related("user", "user__role"):
        mapped = ROLE_TO_LEVEL.get(getattr(getattr(emp.user, "role", None), "name", None))
        lvl = levels.get(mapped[0]) if mapped else None
        if lvl and emp.hierarchy_level_id != lvl.id:
            emp.hierarchy_level = lvl
            emp.save(update_fields=["hierarchy_level"])


def noop(apps, schema_editor):
    """Levels stay put — they're admin-editable rows, not schema."""


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0018_incentiveplan"),
    ]

    operations = [
        migrations.RunPython(seed, noop),
    ]
