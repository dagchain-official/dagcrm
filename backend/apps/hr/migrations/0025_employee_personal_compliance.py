from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0024_employee_photo_document"),
    ]

    operations = [
        migrations.AddField(model_name="employee", name="dob", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="employee", name="nationality", field=models.CharField(blank=True, max_length=60)),
        migrations.AddField(model_name="employee", name="address", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="employee", name="emergency_contact", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="employee", name="emergency_phone", field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name="employee", name="passport_no", field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name="employee", name="passport_expiry", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="employee", name="visa_expiry", field=models.DateField(blank=True, null=True)),
    ]
