# Grant the training modules in the permission matrix so HR (and the management
# roles) can reach them right away. Idempotent.
from django.db import migrations

MODULES = ["training-modules", "training-assignments", "assessments"]
# role -> whether it gets full access; everyone else gets nothing (admin bypasses)
FULL = {"Super Admin", "Business Head", "Sales Director", "HR"}
# sales roles just view the catalogue (their own training)
VIEW = {"Sales Manager", "Team Leader", "Sales Executive"}


def seed(apps, schema_editor):
    ModulePermission = apps.get_model("accounts", "ModulePermission")
    Role = apps.get_model("accounts", "Role")
    for role in Role.objects.all():
        full = role.name in FULL
        view = full or role.name in VIEW
        for module in MODULES:
            # sales roles only see the catalogue, not others' assignments/scores
            can_view = full or (view and module == "training-modules")
            ModulePermission.objects.update_or_create(
                role=role, module=module,
                defaults={"can_view": can_view, "can_create": full,
                          "can_edit": full, "can_delete": full})


def unseed(apps, schema_editor):
    apps.get_model("accounts", "ModulePermission").objects.filter(module__in=MODULES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_companysettings"),
        ("hr", "0021_seed_training_modules"),
    ]
    operations = [migrations.RunPython(seed, unseed)]
