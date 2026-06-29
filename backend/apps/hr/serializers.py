from rest_framework import serializers

from .models import (
    Attendance, CostCategory, Department, Employee, EmployeeActivity, EmployeeCost,
    HierarchyLevel, Incentive, IncentiveRule, Leave, LeaveType, Payroll, TargetMultiplier,
)


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(source="employees.count", read_only=True)

    class Meta:
        model = Department
        fields = ["id", "department_name", "employee_count"]


class CostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCategory
        fields = ["id", "name", "status"]


class EmployeeCostSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = EmployeeCost
        fields = ["id", "employee", "employee_name", "category", "category_name",
                  "amount", "month", "year"]


class HierarchyLevelSerializer(serializers.ModelSerializer):
    employee_count = serializers.IntegerField(source="employees.count", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = HierarchyLevel
        fields = ["id", "level_name", "level_order", "status", "employee_count", "label"]

    def get_label(self, obj):
        return f"{obj.level_order}. {obj.level_name}"


class EmployeeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    department_name = serializers.CharField(source="department.department_name", read_only=True)
    manager_name = serializers.CharField(source="manager.name", read_only=True)
    role_name = serializers.CharField(source="user.role.name", read_only=True)
    hierarchy_level_name = serializers.CharField(source="hierarchy_level.level_name", read_only=True)
    monthly_ctc = serializers.SerializerMethodField()
    # type the person's name/email directly — the login account is auto-created/updated
    name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    role = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Employee
        fields = ["id", "user", "user_name", "name", "email", "role", "role_name",
                  "department", "department_name", "hierarchy_level", "hierarchy_level_name",
                  "designation", "salary", "monthly_ctc", "joining_date", "manager", "manager_name"]
        extra_kwargs = {"user": {"required": False}}

    def get_monthly_ctc(self, obj):
        from django.utils import timezone
        today = timezone.localdate()
        return obj.monthly_ctc(today.month, today.year)

    def validate(self, attrs):
        # a manager must sit ABOVE the employee in the org (smaller level_order)
        level = attrs.get("hierarchy_level") or getattr(self.instance, "hierarchy_level", None)
        manager = attrs.get("manager") or getattr(self.instance, "manager", None)
        if level and manager:
            mgr_emp = Employee.objects.filter(user=manager).select_related("hierarchy_level").first()
            mgr_level = mgr_emp.hierarchy_level if mgr_emp else None
            if mgr_level and mgr_level.level_order >= level.level_order:
                raise serializers.ValidationError(
                    {"manager": f"Manager must be at a higher level than '{level.level_name}'."})
        return attrs

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
    label = serializers.SerializerMethodField()

    class Meta:
        model = IncentiveRule
        fields = ["id", "business", "business_name", "product", "product_name",
                  "formula_type", "formula_value", "label"]

    def get_label(self, obj):
        scope = obj.business.name if obj.business_id else "All businesses"
        if obj.product_id:
            scope += f" · {obj.product.name}"
        val = f"{obj.formula_value}%" if obj.formula_type == "percentage" else f"{obj.formula_value}"
        return f"{scope} — {val} ({obj.formula_type})"


class IncentiveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = Incentive
        fields = ["id", "employee", "employee_name", "rule", "amount", "month", "year"]


class TargetMultiplierSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source="hierarchy_level.level_name", read_only=True)
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = TargetMultiplier
        fields = ["id", "scope", "hierarchy_level", "level_name", "employee",
                  "employee_name", "multiplier", "status", "label"]

    def get_label(self, obj):
        if obj.scope == "employee" and obj.employee_id:
            who = obj.employee.user.name if obj.employee.user else "Employee"
        elif obj.scope == "level" and obj.hierarchy_level_id:
            who = obj.hierarchy_level.level_name
        else:
            who = "All employees"
        return f"{who} — ×{obj.multiplier}"

    def validate(self, attrs):
        scope = attrs.get("scope") or getattr(self.instance, "scope", "global")
        level = attrs.get("hierarchy_level") or getattr(self.instance, "hierarchy_level", None)
        emp = attrs.get("employee") or getattr(self.instance, "employee", None)
        if scope == "level" and not level:
            raise serializers.ValidationError({"hierarchy_level": "Required when scope is 'Hierarchy Level'."})
        if scope == "employee" and not emp:
            raise serializers.ValidationError({"employee": "Required when scope is 'Employee'."})
        if scope == "global":               # keep global rows clean
            attrs["hierarchy_level"] = None
            attrs["employee"] = None
        return attrs
