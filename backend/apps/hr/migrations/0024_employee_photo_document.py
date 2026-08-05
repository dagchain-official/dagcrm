from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0023_attendance_checkin_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="photo",
            field=models.FileField(blank=True, null=True, upload_to="employee_photos/"),
        ),
        migrations.AddField(
            model_name="employee",
            name="document",
            field=models.FileField(blank=True, null=True, upload_to="employee_docs/"),
        ),
    ]
