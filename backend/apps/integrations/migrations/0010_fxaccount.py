from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0028_lead_kyc_status"),
        ("integrations", "0009_fxsymbollots"),
    ]

    operations = [
        migrations.CreateModel(
            name="FxAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(max_length=40, unique=True)),
                ("account_type", models.CharField(blank=True, max_length=40)),
                ("balance", models.FloatField(default=0)),
                ("lots_traded", models.FloatField(default=0)),
                ("gross_brokerage", models.FloatField(default=0)),
                ("ib_commission", models.FloatField(default=0)),
                ("total_deposit", models.FloatField(default=0)),
                ("total_withdrawal", models.FloatField(default=0)),
                ("trading_loss", models.FloatField(default=0)),
                ("kyc_status", models.CharField(blank=True, max_length=30)),
                ("account_status", models.CharField(blank=True, max_length=30)),
                ("opened_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fx_accounts", to="crm.customer")),
            ],
            options={
                "ordering": ["-balance"],
            },
        ),
    ]
