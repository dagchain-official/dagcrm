from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0024_customer_account_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="leadactivity",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
