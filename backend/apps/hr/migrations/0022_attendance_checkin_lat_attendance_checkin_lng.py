from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0021_seed_training_modules"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="checkin_lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="checkin_lng",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
