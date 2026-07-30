from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0025_leadactivity_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="leadactivity",
            name="visit_lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leadactivity",
            name="visit_lng",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leadactivity",
            name="visit_address",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
