# Seed the spec's default incentive schedule (PART 14):
#   Model 1 slabs: 0-100% -> 0%, 100-200% -> 10%, 200-400% -> 20%, 400%+ -> 30%
#   Model 2 activity rewards: Lots Traded x $2, Meetings x $20 (per unit)
from django.db import migrations

SLABS = [
    ("No incentive", 0, 100, 0),
    ("Tier 1", 100, 200, 10),
    ("Tier 2", 200, 400, 20),
    ("Tier 3", 400, None, 30),
]
# (name, metric_key, rate, min_count)
ACTS = [
    ("Lots Traded reward", "lots-traded", 2, 0),
    ("Meetings reward", "meetings", 20, 0),
]


def seed(apps, schema_editor):
    Slab = apps.get_model("hr", "IncentiveSlab")
    Act = apps.get_model("hr", "ActivityIncentive")
    Metric = apps.get_model("crm", "MetricDefinition")
    if not Slab.objects.exists():
        for name, lo, hi, pct in SLABS:
            Slab.objects.create(name=name, min_pct=lo, max_pct=hi,
                                incentive_pct=pct, basis="revenue", status="active")
    for name, key, rate, mc in ACTS:
        if Act.objects.filter(name=name).exists():
            continue
        metric = Metric.objects.filter(key=key).first()
        if metric:
            Act.objects.create(name=name, metric=metric, rate=rate,
                               min_count=mc, status="active")


def unseed(apps, schema_editor):
    apps.get_model("hr", "IncentiveSlab").objects.all().delete()
    apps.get_model("hr", "ActivityIncentive").objects.filter(
        name__in=[a[0] for a in ACTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0012_incentiveslab_activityincentive'),
        ('crm', '0010_seed_metrics'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
