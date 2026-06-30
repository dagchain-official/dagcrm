# Seed the default performance weightage (PART 13): Revenue 60 / Growth 25 /
# Activity 15. Admin can change it or add per-hierarchy-level overrides.
from django.db import migrations


def seed(apps, schema_editor):
    PerformanceWeight = apps.get_model("hr", "PerformanceWeight")
    if not PerformanceWeight.objects.filter(scope="global").exists():
        PerformanceWeight.objects.create(
            scope="global", revenue_weight=60, growth_weight=25,
            activity_weight=15, status="active")


def unseed(apps, schema_editor):
    PerformanceWeight = apps.get_model("hr", "PerformanceWeight")
    PerformanceWeight.objects.filter(scope="global").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0010_performanceweight'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
