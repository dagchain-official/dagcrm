import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0017_jobposting_candidate"),
    ]

    operations = [
        migrations.CreateModel(
            name="IncentivePlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.PositiveSmallIntegerField()),
                ("year", models.PositiveIntegerField()),
                ("incentive_type", models.CharField(choices=[("percentage", "Percentage of target"), ("fixed", "Fixed amount"), ("slab", "Attainment slab")], default="percentage", max_length=20)),
                ("incentive_value", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("slabs", models.JSONField(blank=True, default=list)),
                ("deduction_pct", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("over_pct", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incentive_plans", to="hr.employee")),
            ],
            options={
                "unique_together": {("employee", "month", "year")},
            },
        ),
    ]
