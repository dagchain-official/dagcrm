"""Administration → Users and HR → People are ONE form: whichever endpoint the
person is added from, both the login account and the Employee record are saved.
The org level isn't on the form at all — it follows the role.
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
        self.role = Role.objects.create(name="Sales Executive")     # -> Relationship Manager, 5
        self.head = Role.objects.create(name="Business Head")       # -> Business Head, 1
        self.dept = Department.objects.create(department_name="Sales")

    def _payload(self, **over):
        return {**PAYLOAD, "role": self.role.id, "department": self.dept.id, **over}

    def test_users_form_creates_the_hr_profile(self):
        s = UserSerializer(data=self._payload(name="Form A", email="a@dagos.test"))
        self.assertTrue(s.is_valid(), s.errors)
        u = s.save()

        self.assertEqual(u.employee_id, "EMP-900")
        self.assertEqual(u.phone, "9999900001")
        self.assertEqual(u.status, "active")
        self.assertTrue(u.check_password("secret12345"))

        emp = Employee.objects.get(user=u)
        self.assertEqual(emp.department, self.dept)
        self.assertEqual(str(emp.salary), "42000.00")
        self.assertEqual(str(emp.joining_date), "2026-01-15")
        self.assertEqual(emp.hierarchy_level.level_name, "Relationship Manager")

        # and the HR half reads back into the form for editing
        data = UserSerializer(u).data
        self.assertEqual(data["hierarchy_level_name"], "Relationship Manager")
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
        self.assertEqual(emp.department, self.dept)
        self.assertEqual(emp.hierarchy_level.level_name, "Relationship Manager")

        data = EmployeeSerializer(emp).data
        self.assertEqual(data["employee_id"], "EMP-900")
        self.assertEqual(data["phone"], "9999900001")
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["password"], "")      # never echoed back

    def test_org_level_follows_a_role_change(self):
        for serializer_cls, email in ((UserSerializer, "c@dagos.test"),
                                      (EmployeeSerializer, "d@dagos.test")):
            with self.subTest(form=serializer_cls.__name__):
                s = serializer_cls(data=self._payload(name="Form C", email=email))
                self.assertTrue(s.is_valid(), s.errors)
                obj = s.save()
                emp = obj if isinstance(obj, Employee) else Employee.objects.get(user=obj)
                self.assertEqual(emp.hierarchy_level.level_name, "Relationship Manager")

                s2 = serializer_cls(obj, data={"role": self.head.id}, partial=True)
                self.assertTrue(s2.is_valid(), s2.errors)
                s2.save()
                emp.refresh_from_db()
                self.assertEqual(emp.hierarchy_level.level_name, "Business Head")

    def test_a_submitted_org_level_is_ignored(self):
        bogus = HierarchyLevel.objects.create(level_name="Bogus", level_order=9)
        s = EmployeeSerializer(data=self._payload(
            name="Form G", email="g@dagos.test", hierarchy_level=bogus.id))
        self.assertTrue(s.is_valid(), s.errors)
        emp = s.save()
        self.assertEqual(emp.hierarchy_level.level_name, "Relationship Manager")

    def test_manager_is_kept_in_step_on_both_models(self):
        boss = User.objects.create_user(email="boss@dagos.test", name="Boss",
                                        password="x", role=self.head)
        Employee.objects.create(
            user=boss, hierarchy_level=HierarchyLevel.objects.get(level_name="Business Head"))

        # added from HR → People, manager set on Employee → must land on User too
        s = EmployeeSerializer(data=self._payload(
            name="Form D", email="d2@dagos.test", employee_id="EMP-901", manager=boss.id))
        self.assertTrue(s.is_valid(), s.errors)
        emp = s.save()
        emp.user.refresh_from_db()
        self.assertEqual(emp.manager_id, boss.id)
        self.assertEqual(emp.user.manager_id, boss.id)

        # added from Users, manager set on User → must land on Employee too
        s2 = UserSerializer(data=self._payload(
            name="Form E", email="e@dagos.test", employee_id="EMP-902", manager=boss.id))
        self.assertTrue(s2.is_valid(), s2.errors)
        u2 = s2.save()
        self.assertEqual(Employee.objects.get(user=u2).manager_id, boss.id)

    def test_a_manager_on_the_same_level_is_allowed(self):
        lead = User.objects.create_user(email="lead@dagos.test", name="Senior RM",
                                        password="x", role=self.role)
        Employee.objects.create(
            user=lead,
            hierarchy_level=HierarchyLevel.objects.get(level_name="Relationship Manager"))
        s = EmployeeSerializer(data=self._payload(
            name="Form H", email="h@dagos.test", manager=lead.id))
        self.assertTrue(s.is_valid(), s.errors)

    def test_a_manager_below_the_employee_is_rejected(self):
        junior = User.objects.create_user(email="jr@dagos.test", name="Junior",
                                          password="x", role=self.role)
        Employee.objects.create(
            user=junior,
            hierarchy_level=HierarchyLevel.objects.get(level_name="Relationship Manager"))
        s = EmployeeSerializer(data=self._payload(
            name="Form I", email="i@dagos.test", role=self.head.id, manager=junior.id))
        self.assertFalse(s.is_valid())
        self.assertIn("manager", s.errors)

    def test_password_only_edit_leaves_the_hr_profile_alone(self):
        s = UserSerializer(data=self._payload(name="Form F", email="f@dagos.test"))
        self.assertTrue(s.is_valid(), s.errors)
        u = s.save()

        s2 = UserSerializer(u, data={"password": "newpass12345"}, partial=True)
        self.assertTrue(s2.is_valid(), s2.errors)
        s2.save()

        emp = Employee.objects.get(user=u)
        self.assertEqual(emp.department, self.dept)
        self.assertEqual(str(emp.salary), "42000.00")
        u.refresh_from_db()
        self.assertTrue(u.check_password("newpass12345"))
