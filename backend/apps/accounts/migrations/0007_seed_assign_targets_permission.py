# Who may assign targets became a permission ("assign-targets") instead of a
# hardcoded role list. Seed the matrix row for every existing role so the
# capability is visible and editable in the Permission Matrix from day one.
from django.db import migrations

MODULE = "assign-targets"

# roles that get it switched ON by default — everyone in the management chain.
# Reach is still limited to each person's own subtree (see access.can_assign_to).
DEFAULT_ON = {"Super Admin", "Business Head", "Sales Director",
              "Sales Manager", "Team Leader"}


def seed(apps, schema_editor):
    ModulePermission = apps.get_model("accounts", "ModulePermission")
    Role = apps.get_model("accounts", "Role")
    for role in Role.objects.all():
        ModulePermission.objects.update_or_create(
            role=role, module=MODULE,
            defaults={"can_view": role.name in DEFAULT_ON,
                      "can_create": role.name in DEFAULT_ON,
                      "can_edit": False, "can_delete": False},
        )


def unseed(apps, schema_editor):
    apps.get_model("accounts", "ModulePermission").objects.filter(module=MODULE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_user_onboarding"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
