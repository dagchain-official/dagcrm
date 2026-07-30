from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0022_attendance_checkin_lat_attendance_checkin_lng"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="checkin_address",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
