# Copy the existing User.manager chain onto Employee.manager so the org tree
# has a reporting structure out of the box (admin can edit it afterwards).
from django.db import migrations


def backfill(apps, schema_editor):
    Employee = apps.get_model("hr", "Employee")
    for emp in Employee.objects.select_related("user").all():
        if emp.manager_id:
            continue
        mgr = getattr(emp.user, "manager_id", None)
        if mgr:
            emp.manager_id = mgr
            emp.save(update_fields=["manager"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0004_seed_hierarchy_levels'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
