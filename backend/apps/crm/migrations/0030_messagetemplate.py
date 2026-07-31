from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0029_leadactivity_remind_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("channel", models.CharField(choices=[("whatsapp", "WhatsApp"), ("email", "Email")], default="whatsapp", max_length=20)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("body", models.TextField()),
                ("scope", models.CharField(choices=[("shared", "Shared (everyone)"), ("personal", "Personal (only me)")], default="personal", max_length=10)),
                ("trigger", models.CharField(blank=True, choices=[("", "Manual — pick when sending"), ("call_no_answer", "Auto — call outcome: No Answer"), ("call_busy", "Auto — call outcome: Busy")], max_length=30)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("business", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="crm.business")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="message_templates", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
