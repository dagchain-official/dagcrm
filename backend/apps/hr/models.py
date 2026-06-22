from django.conf import settings
from django.db import models


# ------------------------------------------------------------------ Departments
class Department(models.Model):
    department_name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.department_name


class Employee(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    designation = models.CharField(max_length=120, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    joining_date = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_employees")


# ------------------------------------------------------------------ Attendance
class Attendance(models.Model):
    STATUS = [("present", "Present"), ("absent", "Absent"),
              ("half_day", "Half Day"), ("leave", "Leave")]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance")
    checkin = models.DateTimeField(null=True, blank=True)
    checkout = models.DateTimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="present")
    date = models.DateField()

    class Meta:
        ordering = ["-date"]


class EmployeeActivity(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="activities")
    login_duration = models.PositiveIntegerField(default=0)  # minutes
    active_duration = models.PositiveIntegerField(default=0)  # minutes
    idle_duration = models.PositiveIntegerField(default=0)  # minutes
    calls_completed = models.PositiveIntegerField(default=0)
    notes_added = models.PositiveIntegerField(default=0)
    tickets_updated = models.PositiveIntegerField(default=0)
    date = models.DateField()

    class Meta:
        verbose_name_plural = "Employee activities"
        ordering = ["-date"]


# ------------------------------------------------------------------ Leaves
class LeaveType(models.Model):
    leave_name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.leave_name


class Leave(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")


# ------------------------------------------------------------------ Payroll
class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payrolls")
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    incentive = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ("employee", "month", "year")

    def save(self, *args, **kwargs):
        self.final_salary = self.basic_salary + self.incentive + self.bonus - self.deduction
        super().save(*args, **kwargs)


# ------------------------------------------------------------------ Incentives
class IncentiveRule(models.Model):
    FORMULA_TYPE = [("percentage", "Percentage"), ("fixed", "Fixed"), ("slab", "Slab")]
    business = models.ForeignKey("crm.Business", on_delete=models.CASCADE)
    product = models.ForeignKey("crm.Product", on_delete=models.SET_NULL, null=True, blank=True)
    formula_type = models.CharField(max_length=20, choices=FORMULA_TYPE, default="percentage")
    formula_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Incentive(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="incentives")
    rule = models.ForeignKey(IncentiveRule, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ("employee", "rule", "month", "year")
