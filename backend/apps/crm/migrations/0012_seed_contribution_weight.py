# Seed the default Net Business Contribution formula (PART 12): revenue parts
# +1, trading loss −1, deposit excluded. Admin can edit these multipliers.
from django.db import migrations


def seed(apps, schema_editor):
    W = apps.get_model("crm", "ContributionWeight")
    if not W.objects.exists():
        W.objects.create(deposit=0, trading_loss=-1, brokerage=1,
                         insurance=1, staking=1, other=1)


def unseed(apps, schema_editor):
    apps.get_model("crm", "ContributionWeight").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0011_contributionweight_aumentry_contributionentry'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
