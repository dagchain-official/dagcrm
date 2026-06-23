from rest_framework import serializers

from .models import (
    Attendance, Department, Employee, EmployeeActivity, Incentive, IncentiveRule,
    Leave, LeaveType, Payroll,
)


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(source="employees.count", read_only=True)

    class Meta:
        model = Department
        fields = ["id", "department_name", "employee_count"]


class EmployeeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    department_name = serializers.CharField(source="department.department_name", read_only=True)
    manager_name = serializers.CharField(source="manager.name", read_only=True)
    role_name = serializers.CharField(source="user.role.name", read_only=True)
    # type the person's name/email directly — the login account is auto-created/updated
    name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    role = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Employee
        fields = ["id", "user", "user_name", "name", "email", "role", "role_name",
                  "department", "department_name", "designation", "salary",
                  "joining_date", "manager", "manager_name"]
        extra_kwargs = {"user": {"required": False}}

    def to_representation(self, instance):
        data = super().to_representation(instance)  # name/email/role are write_only here
        u = instance.user if instance.user_id else None
        data["name"] = u.name if u else ""
        data["email"] = u.email if u else ""
        data["role"] = u.role_id if u else None
        return data

    def _apply_role(self, user, role_id):
        from apps.accounts.models import Role
        if role_id and user:
            user.role = Role.objects.filter(id=role_id).first()
            user.save(update_fields=["role"])

    def _gen_email(self, name):
        import re
        slug = re.sub(r"[^a-z0-9]+", ".", (name or "employee").lower()).strip(".")
        return f"{slug or 'employee'}@dagos.com"

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        name = validated_data.pop("name", None)
        email = validated_data.pop("email", None)
        role_id = validated_data.pop("role", None)
        if not validated_data.get("user"):
            if not name:
                raise serializers.ValidationError({"name": "Employee name is required."})
            email = email or self._gen_email(name)
            base, i = email, 1
            while User.objects.filter(email=email).exists():
                email = base.replace("@", f"{i}@"); i += 1
            validated_data["user"] = User.objects.create_user(
                email=email, name=name, password="changeme123")
        self._apply_role(validated_data["user"], role_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)
        email = validated_data.pop("email", None)
        role_id = validated_data.pop("role", None)
        if instance.user and (name or email):
            if name:
                instance.user.name = name
            if email:
                instance.user.email = email
            instance.user.save()
        self._apply_role(instance.user, role_id)
        return super().update(instance, validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "employee", "employee_name", "checkin", "checkout",
                  "working_hours", "status", "date"]


class EmployeeActivitySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = EmployeeActivity
        fields = ["id", "employee", "employee_name", "login_duration", "active_duration",
                  "idle_duration", "calls_completed", "notes_added", "tickets_updated", "date"]


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.leave_name", read_only=True)

    class Meta:
        model = Leave
        fields = ["id", "employee", "employee_name", "leave_type", "leave_type_name",
                  "start_date", "end_date", "reason", "status"]


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = Payroll
        fields = ["id", "employee", "employee_name", "basic_salary", "incentive", "bonus",
                  "deduction", "final_salary", "month", "year"]
        read_only_fields = ["final_salary"]


class IncentiveRuleSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = IncentiveRule
        fields = ["id", "business", "business_name", "product", "product_name",
                  "formula_type", "formula_value"]


class IncentiveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = Incentive
        fields = ["id", "employee", "employee_name", "rule", "amount", "month", "year"]
