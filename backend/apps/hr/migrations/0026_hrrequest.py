from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0025_employee_personal_compliance"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HRRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_type", models.CharField(choices=[("leave", "Leave"), ("visa", "Visa / Immigration"), ("letter", "Letter / Certificate"), ("reimbursement", "Reimbursement"), ("document", "Document"), ("other", "Other")], default="other", max_length=20)),
                ("title", models.CharField(max_length=150)),
                ("details", models.TextField(blank=True)),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled")], default="pending", max_length=12)),
                ("chain", models.JSONField(default=list)),
                ("stage_index", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hr_requests", to="hr.employee")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="HRRequestApproval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage", models.CharField(max_length=20)),
                ("decision", models.CharField(max_length=10)),
                ("comment", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approver", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approvals", to="hr.hrrequest")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
