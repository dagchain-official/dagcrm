from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_emailaccount"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarded",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="onboarding_modules",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
