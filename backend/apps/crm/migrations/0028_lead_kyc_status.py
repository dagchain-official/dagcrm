from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0027_customer_onboarding_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="kyc_status",
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
