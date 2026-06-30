from django.conf import settings
from django.db import models


# ------------------------------------------------------------------ Departments
class Department(models.Model):
    department_name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.department_name


# ---- Dynamic org hierarchy (PART 2) ---------------------------------------
# A SEPARATE dimension from RBAC roles. Roles = permissions (access.py).
# Levels = reporting structure for P&L / target / performance rollups.
# Admin can add / rename / reorder levels with no code changes.
class HierarchyLevel(models.Model):
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    level_name = models.CharField(max_length=80)          # "Business Head", "RM", "Country Head"…
    level_order = models.PositiveIntegerField(default=1)  # 1 = top of the org … N = bottom
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    class Meta:
        ordering = ["level_order"]

    def __str__(self):
        return f"{self.level_order}. {self.level_name}"


class Employee(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    hierarchy_level = models.ForeignKey(HierarchyLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    designation = models.CharField(max_length=120, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # monthly basic — single source (also drives payroll)
    joining_date = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_employees")

    def monthly_ctc(self, month, year):
        """Total Cost To Company = monthly salary + extra costs for that period.
        Salary is NOT duplicated as a cost row — it stays the single source."""
        extra = self.costs.filter(month=month, year=year).aggregate(
            t=models.Sum("amount"))["t"] or 0
        return (self.salary or 0) + extra

    def revenue_target(self, month, year):
        """Revenue target = monthly CTC × configured multiplier (PART 5).
        Multiplier resolves employee > hierarchy-level > global (default 1.0)."""
        return self.monthly_ctc(month, year) * TargetMultiplier.resolve(self)


# ---- Cost Engine (PART 3) -------------------------------------------------
# Configurable cost categories (Visa, Laptop, Internet, Office, Other…).
# Salary is deliberately NOT a category here — it lives on Employee.salary
# (single source of truth, already used by payroll) to avoid double-counting.
class CostCategory(models.Model):
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    name = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    class Meta:
        verbose_name_plural = "Cost categories"

    def __str__(self):
        return self.name


class EmployeeCost(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="costs")
    category = models.ForeignKey(CostCategory, on_delete=models.PROTECT, related_name="costs")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # monthly figure
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()

    class Meta:
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.employee_id} · {self.category.name} · {self.amount}"


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


# ---- Target Engine (PART 5) -----------------------------------------------
# Target = CTC (PART 3) × Multiplier. The multiplier is admin-configurable at
# three scopes; resolution priority is employee override > hierarchy-level
# default > global default (falls back to 1.0 if nothing is configured).
# A manager's headline target rolls up the SUM of their whole team's individual
# targets — their own personal target is not folded in (see reports/targets.py).
class TargetMultiplier(models.Model):
    SCOPE = [("global", "Global"), ("level", "Hierarchy Level"), ("employee", "Employee")]
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    scope = models.CharField(max_length=20, choices=SCOPE, default="global")
    hierarchy_level = models.ForeignKey(
        HierarchyLevel, on_delete=models.CASCADE, null=True, blank=True, related_name="multipliers")
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True, related_name="multipliers")
    multiplier = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    def __str__(self):
        target = (self.employee.user.name if self.scope == "employee" and self.employee_id and self.employee.user
                  else self.hierarchy_level.level_name if self.scope == "level" and self.hierarchy_level_id
                  else "All employees")
        return f"{target} × {self.multiplier}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.scope == "level" and not self.hierarchy_level_id:
            raise ValidationError({"hierarchy_level": "Required when scope is 'Hierarchy Level'."})
        if self.scope == "employee" and not self.employee_id:
            raise ValidationError({"employee": "Required when scope is 'Employee'."})
        if self.scope == "global":          # keep global rows clean
            self.hierarchy_level = None
            self.employee = None

    @staticmethod
    def resolve(employee):
        """Multiplier for one employee: employee > level > global > 1.0."""
        from decimal import Decimal
        q = TargetMultiplier.objects.filter(status="active")
        m = q.filter(scope="employee", employee=employee).first()
        if not m and employee.hierarchy_level_id:
            m = q.filter(scope="level", hierarchy_level_id=employee.hierarchy_level_id).first()
        if not m:
            m = q.filter(scope="global").first()
        return m.multiplier if m else Decimal("1")


# ---- Performance Model (PART 13) ------------------------------------------
# Every employee is scored on 3 independent scorecards — Revenue, Growth,
# Activity — combined into one overall score using admin-configurable weightage
# (e.g. 60 / 25 / 15). Weights resolve per hierarchy-level, else a global row.
# The scoring itself lives in reports/performance.py (peer-normalised, 0-100).
class PerformanceWeight(models.Model):
    SCOPE = [("global", "Global"), ("level", "Hierarchy Level")]
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    scope = models.CharField(max_length=20, choices=SCOPE, default="global")
    hierarchy_level = models.ForeignKey(
        HierarchyLevel, on_delete=models.CASCADE, null=True, blank=True, related_name="perf_weights")
    revenue_weight = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    growth_weight = models.DecimalField(max_digits=5, decimal_places=2, default=25)
    activity_weight = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    def __str__(self):
        who = self.hierarchy_level.level_name if self.scope == "level" and self.hierarchy_level_id else "All"
        return f"{who}: {self.revenue_weight}/{self.growth_weight}/{self.activity_weight}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.scope == "level" and not self.hierarchy_level_id:
            raise ValidationError({"hierarchy_level": "Required when scope is 'Hierarchy Level'."})
        if self.scope == "global":
            self.hierarchy_level = None

    def as_fractions(self):
        """Normalise the 3 weights so they sum to 1.0 (handles any input total)."""
        total = float(self.revenue_weight + self.growth_weight + self.activity_weight) or 1.0
        return (float(self.revenue_weight) / total,
                float(self.growth_weight) / total,
                float(self.activity_weight) / total)

    @staticmethod
    def resolve(employee):
        """Weights for one employee: level override > global > default 60/25/15."""
        q = PerformanceWeight.objects.filter(status="active")
        w = None
        if employee.hierarchy_level_id:
            w = q.filter(scope="level", hierarchy_level_id=employee.hierarchy_level_id).first()
        if not w:
            w = q.filter(scope="global").first()
        if w:
            return w.as_fractions()
        return (0.6, 0.25, 0.15)


# ---- Incentive Engine (PART 14) -------------------------------------------
# Two independent, admin-configurable models that combine into one payout:
#   Model 1  IncentiveSlab    — target-attainment tiers (100-200% -> 10% …)
#   Model 2  ActivityIncentive — per-KPI reward (lots × $2, meetings × $200 …)
# Computation + payout live in reports/incentives.py.
class IncentiveSlab(models.Model):
    """One tier of the target-achievement schedule (Model 1). Attainment in
    [min_pct, max_pct) earns incentive_pct of `basis`."""
    BASIS = [("revenue", "% of revenue generated"), ("target", "% of target value")]
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    name = models.CharField(max_length=80, blank=True)
    min_pct = models.DecimalField(max_digits=7, decimal_places=2, default=0)        # attainment >= this
    max_pct = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)  # < this; blank = ∞
    incentive_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    basis = models.CharField(max_length=10, choices=BASIS, default="revenue")
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    class Meta:
        ordering = ["min_pct"]

    def __str__(self):
        hi = f"{self.max_pct}%" if self.max_pct is not None else "∞"
        return f"{self.min_pct}%–{hi} → {self.incentive_pct}%"


class ActivityIncentive(models.Model):
    """Per-unit reward on any configured KPI (Model 2). Pays rate × metric value
    for the period, once the value reaches min_count."""
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    name = models.CharField(max_length=80)
    metric = models.ForeignKey("crm.MetricDefinition", on_delete=models.CASCADE, related_name="incentives")
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)          # amount per unit
    min_count = models.DecimalField(max_digits=12, decimal_places=2, default=0)     # pay only if value >= this
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    def __str__(self):
        return f"{self.name}: {self.rate} per {self.metric.unit or 'unit'}"
