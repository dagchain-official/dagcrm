# Seed a few sample KPIs (PART 6) so the engine is usable out of the box.
# Historical models don't run the custom save()/slug logic, so `key` is explicit.
from django.db import migrations

# (business_name | None, name, key, unit, aggregation, category, source, derived_key)
DEFS = [
    (None, "Meetings", "meetings", "count", "count", "activity", "derived", "lead_activity:meeting"),
    (None, "Calls", "calls", "count", "count", "activity", "derived", "lead_activity:call"),
    (None, "Leads Converted", "leads-converted", "count", "count", "growth", "derived", "lead:converted"),
    ("FX Artha", "Lots Traded", "lots-traded", "lots", "sum", "activity", "manual", ""),
    ("FX Artha", "New Deposits", "new-deposits", "$", "sum", "growth", "manual", ""),
    ("FX Artha", "Active Traders", "active-traders", "count", "latest", "growth", "manual", ""),
    ("DAGChain", "Nodes Sold", "nodes-sold", "count", "sum", "growth", "manual", ""),
    ("DAGChain", "Storage Sold", "storage-sold", "GB", "sum", "growth", "manual", ""),
    ("DAG Army", "Students Enrolled", "students-enrolled", "count", "sum", "growth", "manual", ""),
]


def seed(apps, schema_editor):
    Business = apps.get_model("crm", "Business")
    Metric = apps.get_model("crm", "MetricDefinition")
    for bn, name, key, unit, agg, cat, src, dkey in DEFS:
        if Metric.objects.filter(key=key).exists():
            continue
        biz = Business.objects.filter(name=bn).first() if bn else None
        if bn and not biz:           # business not seeded in this DB — skip
            continue
        Metric.objects.create(
            name=name, key=key, business=biz, unit=unit, aggregation=agg,
            category=cat, source=src, derived_key=dkey, status="active")


def unseed(apps, schema_editor):
    Metric = apps.get_model("crm", "MetricDefinition")
    Metric.objects.filter(key__in=[d[2] for d in DEFS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0009_metricdefinition_metricentry'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
