# Seed a single global target multiplier (Target = CTC × multiplier, PART 5).
# Default 2.0x — admin can change it or add level/employee overrides.
from django.db import migrations


def seed(apps, schema_editor):
    TargetMultiplier = apps.get_model("hr", "TargetMultiplier")
    if not TargetMultiplier.objects.filter(scope="global").exists():
        TargetMultiplier.objects.create(scope="global", multiplier=2, status="active")


def unseed(apps, schema_editor):
    TargetMultiplier = apps.get_model("hr", "TargetMultiplier")
    TargetMultiplier.objects.filter(scope="global", multiplier=2).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0008_targetmultiplier'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
