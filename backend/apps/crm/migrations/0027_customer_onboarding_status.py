from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0026_leadactivity_visit"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="kyc_status",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="customer",
            name="account_status",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="customer",
            name="account_opened_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
