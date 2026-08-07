from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hr", "0028_profilechangerequest"),
    ]

    operations = [
        # S2 — HR request owner + due date
        migrations.AddField(
            model_name="hrrequest",
            name="owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="hr_requests_owned", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="hrrequest",
            name="due_date",
            field=models.DateField(blank=True, null=True),
        ),
        # S8 — monthly review / acknowledge on Appraisal
        migrations.AddField(
            model_name="appraisal",
            name="source",
            field=models.CharField(default="manual", max_length=12),
        ),
        migrations.AddField(
            model_name="appraisal",
            name="employee_ack",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appraisal",
            name="acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # S4 — counter-sign on Policy / PolicyAcknowledgement
        migrations.AddField(
            model_name="policy",
            name="requires_countersign",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="policyacknowledgement",
            name="counter_signed_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="policy_countersigns", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="policyacknowledgement",
            name="counter_signature",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="policyacknowledgement",
            name="counter_signed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="policyacknowledgement",
            name="archived",
            field=models.BooleanField(default=False),
        ),
        # S5 — Visa milestone tracker
        migrations.CreateModel(
            name="VisaCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visa_type", models.CharField(blank=True, max_length=60)),
                ("reference", models.CharField(blank=True, max_length=80)),
                ("stage", models.CharField(choices=[("applied", "Applied"), ("documents", "Documents"), ("medical", "Medical"), ("biometrics", "Biometrics"), ("submitted", "Submitted"), ("approved", "Approved"), ("stamped", "Stamped"), ("rejected", "Rejected")], default="applied", max_length=20)),
                ("applied_date", models.DateField(blank=True, null=True)),
                ("expected_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="visa_cases", to="hr.employee")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
