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

    class Meta:
        model = Employee
        fields = ["id", "user", "user_name", "department", "department_name", "designation",
                  "salary", "joining_date", "manager", "manager_name"]


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
