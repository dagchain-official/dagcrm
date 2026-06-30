# Seed the spec's example formula rules (PART 16). Structured, not eval.
from django.db import migrations

# (rule fields, [conditions])
RULES = [
    (dict(name="Revenue beats 2× cost", match="all", payout_type="percent",
          payout_on="revenue", payout_value=10, priority=10),
     [dict(left="revenue", operator="gt", right_type="variable",
           right_variable="cost", right_factor=2)]),
    (dict(name="Lots reward", match="all", payout_type="per_unit",
          payout_on="kpi:lots-traded", payout_value=2, priority=20),
     [dict(left="kpi:lots-traded", operator="gt", right_type="constant", right_value=100)]),
    (dict(name="Meeting bonus", match="all", payout_type="flat",
          payout_on="", payout_value=200, priority=30),
     [dict(left="kpi:meetings", operator="gt", right_type="constant", right_value=10)]),
]


def seed(apps, schema_editor):
    Rule = apps.get_model("hr", "FormulaRule")
    Cond = apps.get_model("hr", "FormulaCondition")
    for rdata, conds in RULES:
        if Rule.objects.filter(name=rdata["name"]).exists():
            continue
        rule = Rule.objects.create(status="active", **rdata)
        for c in conds:
            Cond.objects.create(rule=rule, **c)


def unseed(apps, schema_editor):
    apps.get_model("hr", "FormulaRule").objects.filter(
        name__in=[r[0]["name"] for r in RULES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0014_formularule_formulacondition'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
