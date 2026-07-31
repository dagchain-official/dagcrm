from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0028_lead_kyc_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="leadactivity",
            name="remind_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
