# Seed default cost categories. Salary is intentionally excluded — it lives on
# Employee.salary (single source, also drives payroll) to avoid double-counting.
from django.db import migrations

DEFAULTS = ["Visa", "Laptop", "Internet", "Office", "Other"]


def seed(apps, schema_editor):
    CostCategory = apps.get_model("hr", "CostCategory")
    for name in DEFAULTS:
        CostCategory.objects.get_or_create(name=name, defaults={"status": "active"})


def unseed(apps, schema_editor):
    CostCategory = apps.get_model("hr", "CostCategory")
    CostCategory.objects.filter(name__in=DEFAULTS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0006_costcategory_employeecost'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
