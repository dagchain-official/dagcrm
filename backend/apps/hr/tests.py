"""Administration → Users and HR → People are ONE form: whichever endpoint the
person is added from, both the login account and the Employee record are saved.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role
from apps.accounts.serializers import UserSerializer
from apps.hr.models import Department, Employee, HierarchyLevel
from apps.hr.serializers import EmployeeSerializer

User = get_user_model()

PAYLOAD = {
    "employee_id": "EMP-900", "phone": "9999900001",
    "salary": "42000", "joining_date": "2026-01-15",
    "status": "active", "password": "secret12345",
}


class CommonPersonFormTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="Relationship Manager")
        self.lvl = HierarchyLevel.objects.create(level_name="RM", level_order=4)
        self.dept = Department.objects.create(department_name="Sales")

    def _payload(self, **over):
        return {**PAYLOAD, "role": self.role.id, "hierarchy_level": self.lvl.id,
                "department": self.dept.id, **over}

    def test_users_form_creates_the_hr_profile(self):
        s = UserSerializer(data=self._payload(name="Form A", email="a@dagos.test"))
        self.assertTrue(s.is_valid(), s.errors)
        u = s.save()

        self.assertEqual(u.employee_id, "EMP-900")
        self.assertEqual(u.phone, "9999900001")
        self.assertEqual(u.status, "active")
        self.assertTrue(u.check_password("secret12345"))

        emp = Employee.objects.get(user=u)
        self.assertEqual(emp.hierarchy_level, self.lvl)
        self.assertEqual(emp.department, self.dept)
        self.assertEqual(str(emp.salary), "42000.00")
        self.assertEqual(str(emp.joining_date), "2026-01-15")

        # and the HR half reads back into the form for editing
        data = UserSerializer(u).data
        self.assertEqual(data["hierarchy_level"], self.lvl.id)
        self.assertEqual(data["hierarchy_level_name"], "RM")
        self.assertEqual(data["department"], self.dept.id)
        self.assertEqual(data["joining_date"], "2026-01-15")

    def test_people_form_creates_the_login_account(self):
        s = EmployeeSerializer(data=self._payload(name="Form B", email="b@dagos.test"))
        self.assertTrue(s.is_valid(), s.errors)
        emp = s.save()
        u = emp.user

        self.assertEqual(u.name, "Form B")
        self.assertEqual(u.email, "b@dagos.test")
        self.assertEqual(u.employee_id, "EMP-900")
        self.assertEqual(u.phone, "9999900001")
        self.assertEqual(u.status, "active")
        self.assertEqual(u.role, self.role)
        self.assertTrue(u.check_password("secret12345"))
        self.assertEqual(emp.hierarchy_level, self.lvl)
        self.assertEqual(emp.department, self.dept)

        data = EmployeeSerializer(emp).data
        self.assertEqual(data["employee_id"], "EMP-900")
        self.assertEqual(data["phone"], "9999900001")
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["password"], "")      # never echoed back

    def test_manager_is_kept_in_step_on_both_models(self):
        boss_lvl = HierarchyLevel.objects.create(level_name="Head", level_order=1)
        boss = User.objects.create_user(email="boss@dagos.test", name="Boss", password="x")
        Employee.objects.create(user=boss, hierarchy_level=boss_lvl)

        # added from HR → People, manager set on Employee → must land on User too
        s = EmployeeSerializer(data=self._payload(
            name="Form C", email="c@dagos.test", employee_id="EMP-901", manager=boss.id))
        self.assertTrue(s.is_valid(), s.errors)
        emp = s.save()
        emp.user.refresh_from_db()
        self.assertEqual(emp.manager_id, boss.id)
        self.assertEqual(emp.user.manager_id, boss.id)

        # added from Users, manager set on User → must land on Employee too
        s2 = UserSerializer(data=self._payload(
            name="Form D", email="d@dagos.test", employee_id="EMP-902", manager=boss.id))
        self.assertTrue(s2.is_valid(), s2.errors)
        u2 = s2.save()
        self.assertEqual(Employee.objects.get(user=u2).manager_id, boss.id)

    def test_password_only_edit_leaves_the_hr_profile_alone(self):
        s = UserSerializer(data=self._payload(name="Form E", email="e@dagos.test"))
        self.assertTrue(s.is_valid(), s.errors)
        u = s.save()

        s2 = UserSerializer(u, data={"password": "newpass12345"}, partial=True)
        self.assertTrue(s2.is_valid(), s2.errors)
        s2.save()

        emp = Employee.objects.get(user=u)
        self.assertEqual(emp.hierarchy_level, self.lvl)     # untouched
        self.assertEqual(emp.department, self.dept)
        u.refresh_from_db()
        self.assertTrue(u.check_password("newpass12345"))

    def test_unknown_org_level_is_rejected(self):
        s = UserSerializer(data=self._payload(
            name="Form F", email="f@dagos.test", hierarchy_level=999999))
        self.assertFalse(s.is_valid())
        self.assertIn("hierarchy_level", s.errors)
