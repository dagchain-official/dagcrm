# Seed the lead sources the client uses (from the Excel monitor). Idempotent —
# only adds missing ones, never touches existing rows or their leads.
from django.db import migrations

SOURCES = [
    "Company Lead", "Self Lead", "Employee Referral", "Customer Referral",
    "Website", "Google Ads", "Meta Ads", "WhatsApp", "Walk-in", "Cold Data",
    "Event", "Partner",
]


def seed(apps, schema_editor):
    LeadSource = apps.get_model("crm", "LeadSource")
    for name in SOURCES:
        LeadSource.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    # leave them — removing could orphan leads that reference them
    pass


class Migration(migrations.Migration):

    dependencies = [("crm", "0018_customer_assigned_to")]
    operations = [migrations.RunPython(seed, unseed)]
