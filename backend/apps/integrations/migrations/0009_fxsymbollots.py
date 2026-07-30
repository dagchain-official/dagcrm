from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0026_leadactivity_visit"),
        ("integrations", "0008_commissionrule_basis"),
    ]

    operations = [
        migrations.CreateModel(
            name="FxSymbolLots",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(max_length=40)),
                ("lots", models.FloatField(default=0)),
                ("brokerage", models.FloatField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="symbol_lots", to="crm.customer")),
            ],
            options={
                "ordering": ["-lots"],
                "unique_together": {("customer", "symbol")},
            },
        ),
    ]
