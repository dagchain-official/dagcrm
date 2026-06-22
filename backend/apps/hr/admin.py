from django.contrib import admin

from .models import (
    Attendance, Department, Employee, EmployeeActivity, Incentive, IncentiveRule,
    Leave, LeaveType, Payroll,
)

admin.site.register([
    Department, Employee, Attendance, EmployeeActivity, LeaveType, Leave,
    Payroll, IncentiveRule, Incentive,
])
