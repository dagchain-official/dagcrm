from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.access import MODULES, ROLE_MATRIX, ROLES
from apps.accounts.models import ModulePermission, Role, UserPermission
from apps.crm.models import Business
from apps.hr.models import LeaveType

User = get_user_model()

DEMO_USERS = [
    ("bh@dagos.com", "Business Head", "Bilal Head", None),
    ("smgr@dagos.com", "Sales Manager", "Sara Manager", "bh@dagos.com"),
    ("tl@dagos.com", "Team Leader", "Tariq Leader", "smgr@dagos.com"),
    ("rm.a@dagos.com", "Sales Executive", "Rao A (limited)", "tl@dagos.com"),
    ("rm.b@dagos.com", "Sales Executive", "Rao B (full)", "tl@dagos.com"),
    ("support@dagos.com", "Support", "Sana Support", None),
    ("hr@dagos.com", "HR", "Hina HR", None),
    ("finance@dagos.com", "Finance", "Faisal Finance", None),
]


class Command(BaseCommand):
    help = "Set up roles, the permission matrix, and demo users for each role."

    def handle(self, *args, **opts):
        # 1) Roles
        roles = {}
        for name in ROLES:
            roles[name] = Role.objects.get_or_create(name=name)[0]
        self.stdout.write(f"Roles ensured: {len(roles)}")

        # 2) Permission matrix (Layer 3)
        count = 0
        for role_name, modules in ROLE_MATRIX.items():
            role = roles[role_name]
            for module in MODULES:
                actions = modules.get(module, "")
                ModulePermission.objects.update_or_create(
                    role=role, module=module,
                    defaults=dict(
                        can_view="v" in actions, can_create="c" in actions,
                        can_edit="e" in actions, can_delete="d" in actions,
                    ),
                )
                count += 1
        self.stdout.write(f"Module permissions set: {count}")

        # 3) Demo users
        created = 0
        for email, role_name, name, mgr_email in DEMO_USERS:
            mgr = User.objects.filter(email=mgr_email).first() if mgr_email else None
            u, was_new = User.objects.get_or_create(
                email=email,
                defaults=dict(name=name, role=roles[role_name], manager=mgr,
                              employee_id=email.split("@")[0].upper()),
            )
            if was_new:
                u.set_password("demo123")
            u.role = roles[role_name]
            u.manager = mgr
            u.save()
            created += was_new
        self.stdout.write(f"Demo users ready ({created} new). Password: demo123")

        # 4) Layer 2 demo — restrict rm.a to first 3 businesses
        rm_a = User.objects.filter(email="rm.a@dagos.com").first()
        biz = list(Business.objects.order_by("id")[:3])
        if rm_a and biz:
            UserPermission.objects.filter(user=rm_a).delete()
            for b in biz:
                UserPermission.objects.create(user=rm_a, business=b, can_view=True,
                                              can_create=True, can_edit=True)
            self.stdout.write(f"rm.a restricted to businesses: {[b.name for b in biz]}")

        # 5) Standard leave types (needed by the My Leaves apply form)
        for name in ["Casual", "Sick", "Earned", "Unpaid", "Maternity Leave", "Work From Home"]:
            LeaveType.objects.get_or_create(leave_name=name)

        self.stdout.write(self.style.SUCCESS("Access setup complete."))
