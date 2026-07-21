from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0003_dagchainnode_dagchainprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="dagchainnode",
            name="staked_amount",
            field=models.DecimalField(decimal_places=6, default=0, max_digits=22),
        ),
        migrations.AddField(
            model_name="dagchainnode",
            name="staking_requirement",
            field=models.DecimalField(decimal_places=6, default=0, max_digits=22),
        ),
    ]
