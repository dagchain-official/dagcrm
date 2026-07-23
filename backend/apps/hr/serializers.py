from rest_framework import serializers

from .models import (
    Attendance, Candidate, CostCategory, Department, Employee, EmployeeActivity, EmployeeCost,
    ActivityIncentive, FormulaCondition, FormulaRule, HierarchyLevel, Incentive, IncentiveRule,
    IncentiveSlab, JobPosting, Leave, LeaveType, Payroll, PerformanceWeight, TargetMultiplier,
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
    # login-account fields, so ONE form creates both the person and their login
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    employee_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    status = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = ["id", "user", "user_name", "name", "email", "role", "role_name",
                  "phone", "employee_id", "password", "status",
                  "department", "department_name", "hierarchy_level", "hierarchy_level_name",
                  "designation", "salary", "monthly_ctc", "joining_date", "manager", "manager_name"]
        # hierarchy_level is derived from the role, never posted from the form
        extra_kwargs = {"user": {"required": False}, "hierarchy_level": {"read_only": True}}

    def get_monthly_ctc(self, obj):
        from django.utils import timezone
        today = timezone.localdate()
        return obj.monthly_ctc(today.month, today.year)

    def _derived_level(self, attrs):
        """The level this employee will end up on, from the role being saved."""
        from apps.accounts.models import Role
        from apps.hr.models import level_for_role
        role_id = attrs.get("role")
        if not role_id and self.instance and self.instance.user_id:
            role_id = self.instance.user.role_id
        name = (Role.objects.filter(id=role_id).values_list("name", flat=True).first()
                if role_id else None)
        return level_for_role(name)

    def validate(self, attrs):
        # A manager may not sit BELOW the employee in the org. Same level is
        # allowed — levels are derived from the role now, so an HR lead managing
        # HR staff (or a senior RM leading RMs) is a normal, valid setup.
        level = self._derived_level(attrs) or getattr(self.instance, "hierarchy_level", None)
        manager = attrs.get("manager") or getattr(self.instance, "manager", None)
        own_user = attrs.get("user") or getattr(self.instance, "user", None)
        if manager and own_user and manager.id == own_user.id:
            raise serializers.ValidationError({"manager": "Someone can't report to themselves."})
        if level and manager:
            mgr_emp = Employee.objects.filter(user=manager).select_related("hierarchy_level").first()
            mgr_level = mgr_emp.hierarchy_level if mgr_emp else None
            if mgr_level and mgr_level.level_order > level.level_order:
                raise serializers.ValidationError(
                    {"manager": f"Manager sits below '{level.level_name}' in the org."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)  # name/email/role are write_only here
        u = instance.user if instance.user_id else None
        data["name"] = u.name if u else ""
        data["email"] = u.email if u else ""
        data["role"] = u.role_id if u else None
        data["phone"] = u.phone if u else ""
        data["employee_id"] = u.employee_id if u else ""
        data["status"] = u.status if u else ""
        data["password"] = ""            # never echo a password back
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

    def _apply_account(self, user, phone, employee_id, status, password):
        """Push the login-account fields onto the linked user."""
        if not user:
            return
        if phone:
            user.phone = phone
        if employee_id:
            user.employee_id = employee_id
        if status:
            user.status = status
        if password:
            user.set_password(password)
        user.save()

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        name = validated_data.pop("name", None)
        email = validated_data.pop("email", None)
        role_id = validated_data.pop("role", None)
        phone = validated_data.pop("phone", "")
        employee_id = validated_data.pop("employee_id", "")
        password = validated_data.pop("password", "")
        status = validated_data.pop("status", "")
        if not validated_data.get("user"):
            if not name:
                raise serializers.ValidationError({"name": "Employee name is required."})
            email = email or self._gen_email(name)
            base, i = email, 1
            while User.objects.filter(email=email).exists():
                email = base.replace("@", f"{i}@"); i += 1
            validated_data["user"] = User.objects.create_user(
                email=email, name=name, password=password or "changeme123")
        self._apply_role(validated_data["user"], role_id)
        self._apply_account(validated_data["user"], phone, employee_id, status, password)
        return self._sync_level(self._sync_manager(super().create(validated_data)))

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)
        email = validated_data.pop("email", None)
        role_id = validated_data.pop("role", None)
        phone = validated_data.pop("phone", "")
        employee_id = validated_data.pop("employee_id", "")
        password = validated_data.pop("password", "")
        status = validated_data.pop("status", "")
        if instance.user and (name or email):
            if name:
                instance.user.name = name
            if email:
                instance.user.email = email
            instance.user.save()
        self._apply_role(instance.user, role_id)
        self._apply_account(instance.user, phone, employee_id, status, password)
        return self._sync_level(self._sync_manager(super().update(instance, validated_data)))

    def _sync_level(self, emp):
        """Org level follows the role — change someone's role and they move."""
        from apps.hr.models import level_for_role
        name = getattr(getattr(emp.user, "role", None), "name", None) if emp.user_id else None
        lvl = level_for_role(name)
        if lvl and emp.hierarchy_level_id != lvl.id:
            emp.hierarchy_level = lvl
            emp.save(update_fields=["hierarchy_level"])
        return emp

    def _sync_manager(self, emp):
        """Keep User.manager in step with Employee.manager — the Users page reads
        the one, the org tree walks the other, and both forms are now the same."""
        if emp.user_id and emp.user.manager_id != emp.manager_id:
            emp.user.manager_id = emp.manager_id
            emp.user.save(update_fields=["manager"])
        return emp


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


class IncentiveSlabSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = IncentiveSlab
        fields = ["id", "name", "min_pct", "max_pct", "incentive_pct", "basis", "status", "label"]

    def get_label(self, obj):
        hi = f"{obj.max_pct}%" if obj.max_pct is not None else "∞"
        return f"{obj.min_pct}%–{hi} → {obj.incentive_pct}% of {obj.basis}"


class ActivityIncentiveSerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source="metric.name", read_only=True)
    unit = serializers.CharField(source="metric.unit", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = ActivityIncentive
        fields = ["id", "name", "metric", "metric_name", "unit", "rate", "min_count", "status", "label"]

    def get_label(self, obj):
        return f"{obj.name} — {obj.rate} per {obj.metric.unit or 'unit'}"


class FormulaConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaCondition
        fields = ["id", "left", "operator", "right_type", "right_value",
                  "right_value2", "right_variable", "right_factor"]


class FormulaRuleSerializer(serializers.ModelSerializer):
    conditions = FormulaConditionSerializer(many=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = FormulaRule
        fields = ["id", "name", "match", "payout_type", "payout_on", "payout_value",
                  "priority", "status", "conditions", "label"]

    def get_label(self, obj):
        from apps.reports.formulas import rule_label
        return rule_label(obj)

    def create(self, validated_data):
        conds = validated_data.pop("conditions", [])
        rule = FormulaRule.objects.create(**validated_data)
        for c in conds:
            FormulaCondition.objects.create(rule=rule, **c)
        return rule

    def update(self, instance, validated_data):
        conds = validated_data.pop("conditions", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if conds is not None:                 # replace the whole condition set
            instance.conditions.all().delete()
            for c in conds:
                FormulaCondition.objects.create(rule=instance, **c)
        return instance


class PerformanceWeightSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source="hierarchy_level.level_name", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceWeight
        fields = ["id", "scope", "hierarchy_level", "level_name", "revenue_weight",
                  "growth_weight", "activity_weight", "status", "label"]

    def get_label(self, obj):
        who = obj.hierarchy_level.level_name if obj.scope == "level" and obj.hierarchy_level_id else "All employees"
        return f"{who} — R{obj.revenue_weight}/G{obj.growth_weight}/A{obj.activity_weight}"

    def validate(self, attrs):
        scope = attrs.get("scope") or getattr(self.instance, "scope", "global")
        level = attrs.get("hierarchy_level") or getattr(self.instance, "hierarchy_level", None)
        if scope == "level" and not level:
            raise serializers.ValidationError({"hierarchy_level": "Required when scope is 'Hierarchy Level'."})
        if scope == "global":
            attrs["hierarchy_level"] = None
        return attrs


class JobPostingSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    department_name = serializers.CharField(source="department.department_name", read_only=True)
    candidate_count = serializers.IntegerField(source="candidates.count", read_only=True)
    shortlisted_count = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = ["id", "title", "role_name", "business", "business_name", "department",
                  "department_name", "location", "experience", "description",
                  "required_skills", "min_match_pct", "public_token", "status",
                  "candidate_count", "shortlisted_count", "created_at"]
        read_only_fields = ["public_token", "created_at"]

    def get_shortlisted_count(self, obj):
        return obj.candidates.filter(status__in=["shortlisted", "hired"]).count()


class CandidateSerializer(serializers.ModelSerializer):
    resume_url = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Candidate
        fields = ["id", "job", "job_title", "name", "email", "phone", "resume", "resume_url",
                  "match_pct", "matched_skills", "missing_skills", "status", "note", "created_at"]
        read_only_fields = ["match_pct", "matched_skills", "missing_skills", "created_at"]
        extra_kwargs = {"resume": {"write_only": True, "required": False}}

    def get_resume_url(self, obj):
        request = self.context.get("request")
        if obj.resume and request:
            return request.build_absolute_uri(obj.resume.url)
        return None
