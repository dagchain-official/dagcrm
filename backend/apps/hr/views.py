from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import can_manage_all_leaves
from apps.notifications.models import notify

User = get_user_model()

from apps.accounts.scoping import BusinessScopedMixin

from .models import (
    Attendance, Candidate, CostCategory, Department, Employee, EmployeeActivity, EmployeeCost,
    ActivityIncentive, FormulaRule, HierarchyLevel, Incentive, IncentiveRule, IncentiveSlab,
    JobPosting, Leave, LeaveType, Payroll, PerformanceWeight, TargetMultiplier,
)
from .services import today_activity, today_attendance


def _att_payload(att):
    checkin = att.checkin
    worked = float(att.working_hours or 0)
    if checkin and not att.checkout:
        worked = round((timezone.now() - checkin).total_seconds() / 3600, 2)
    return {
        "date": att.date,
        "checked_in": bool(checkin),
        "checked_out": bool(att.checkout),
        "checkin": checkin,
        "checkout": att.checkout,
        "working_hours": worked,
        "status": att.status,
    }


def _act_payload(act):
    return {
        "login_duration": act.login_duration,
        "active_duration": act.active_duration,
        "idle_duration": act.idle_duration,
        "calls_completed": act.calls_completed,
        "notes_added": act.notes_added,
        "tickets_updated": act.tickets_updated,
    }


def reverse_geocode(lat, lng):
    """lat/lng -> human address via OpenStreetMap Nominatim (free, best-effort)."""
    try:
        import requests
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json", "zoom": 18},
            headers={"User-Agent": "DAGOS-CRM/1.0"},
            timeout=6,
        )
        return (r.json().get("display_name") or "")[:300]
    except Exception:
        return ""


class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_superuser:
            return Response({"detail": "Attendance is not applicable for admin."}, status=400)
        att = today_attendance(request.user)
        if not att.checkin:
            att.checkin = timezone.now()
            att.checkout = None
            att.status = "present"
            # geolocation captured by the browser at clock-in (optional)
            try:
                att.checkin_lat = float(request.data.get("lat"))
                att.checkin_lng = float(request.data.get("lng"))
                att.checkin_address = reverse_geocode(att.checkin_lat, att.checkin_lng)
            except (TypeError, ValueError):
                pass
            att.save()
        return Response(_att_payload(att))


class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        att = today_attendance(request.user)
        if att.checkin and not att.checkout:
            att.checkout = timezone.now()
            att.working_hours = round((att.checkout - att.checkin).total_seconds() / 3600, 2)
            att.save()
        return Response(_att_payload(att))


class AttendanceTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        att = today_attendance(request.user)
        if not att:
            return Response({"detail": "Not applicable", "checked_in": False, "checked_out": False})
        return Response(_att_payload(att))


class ActivityTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        act = today_activity(request.user)
        if not act:
            return Response({"detail": "Not applicable"})
        return Response(_act_payload(act))


class ActivityHeartbeatView(APIView):
    """Frontend pings this every minute with active/idle flags (minute resolution)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_superuser:
            return Response({"detail": "Activity not tracked for admin."}, status=200)
        act = today_activity(request.user)
        active = 1 if request.data.get("active") else 0
        act.login_duration += 1
        act.active_duration += active
        act.idle_duration += (1 - active)
        act.save(update_fields=["login_duration", "active_duration", "idle_duration"])
        return Response(_act_payload(act))


class MyLeavesView(APIView):
    """Self-service: any employee applies for / views their OWN leaves."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services import ensure_employee
        emp = ensure_employee(request.user)
        leaves = Leave.objects.filter(employee=emp).select_related("leave_type")
        types = LeaveType.objects.all()
        return Response({
            "leaves": LeaveSerializer(leaves, many=True).data,
            "leave_types": [{"id": t.id, "leave_name": t.leave_name} for t in types],
        })

    def post(self, request):
        from .services import ensure_employee
        if request.user.is_superuser:
            return Response({"detail": "Admin does not apply for leave."}, status=400)
        emp = ensure_employee(request.user)
        data = request.data
        if not data.get("start_date") or not data.get("end_date"):
            return Response({"detail": "Start and end dates are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        leave = Leave.objects.create(
            employee=emp,
            leave_type_id=data.get("leave_type") or None,
            start_date=data["start_date"], end_date=data["end_date"],
            reason=data.get("reason", ""), status="pending",
        )
        # notify the applicant's manager (and HR see it in their queue)
        if request.user.manager_id:
            notify(request.user.manager,
                   title="Leave request",
                   body=f"{request.user.name} requested leave {leave.start_date} → {leave.end_date}.",
                   kind="info", link="/m/leaves")
        return Response(LeaveSerializer(leave).data, status=status.HTTP_201_CREATED)
from .serializers import (
    AttendanceSerializer, CostCategorySerializer, DepartmentSerializer,
    EmployeeActivitySerializer, EmployeeCostSerializer, EmployeeSerializer,
    HierarchyLevelSerializer, IncentiveRuleSerializer, IncentiveSerializer,
    ActivityIncentiveSerializer, FormulaRuleSerializer, IncentiveSlabSerializer, LeaveSerializer,
    LeaveTypeSerializer, PayrollSerializer, PerformanceWeightSerializer, TargetMultiplierSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.prefetch_related("employees").all()
    serializer_class = DepartmentSerializer
    search_fields = ["department_name"]


class HierarchyLevelViewSet(viewsets.ModelViewSet):
    queryset = HierarchyLevel.objects.all()
    serializer_class = HierarchyLevelSerializer
    search_fields = ["level_name"]

    @action(detail=False, methods=["get"])
    def tree(self, request):
        """Org chart — employees nested by their manager chain (top-down)."""
        emps = (Employee.objects.select_related("user", "hierarchy_level", "manager")
                .exclude(user__is_superuser=True))
        children = {}
        for e in emps:
            children.setdefault(e.manager_id, []).append(e)

        def node(e):
            return {
                "id": e.id, "name": e.user.name if e.user else "—",
                "level": e.hierarchy_level.level_name if e.hierarchy_level else None,
                "level_order": e.hierarchy_level.level_order if e.hierarchy_level else 999,
                "reports": sorted(
                    [node(c) for c in children.get(e.user_id, [])],
                    key=lambda n: n["level_order"]),
            }
        roots = [e for e in emps if not e.manager_id or e.manager_id not in
                 {x.user_id for x in emps}]
        tree = sorted([node(e) for e in roots], key=lambda n: n["level_order"])
        return Response({"tree": tree})


class CostCategoryViewSet(viewsets.ModelViewSet):
    queryset = CostCategory.objects.all()
    serializer_class = CostCategorySerializer
    search_fields = ["name"]


class EmployeeCostViewSet(viewsets.ModelViewSet):
    queryset = EmployeeCost.objects.select_related("employee", "employee__user", "category")
    serializer_class = EmployeeCostSerializer
    filterset_fields = ["employee", "category", "month", "year"]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "department", "manager", "hierarchy_level").exclude(user__is_superuser=True)
    serializer_class = EmployeeSerializer
    filterset_fields = ["department", "manager", "hierarchy_level"]
    search_fields = ["user__name", "designation"]

    def get_queryset(self):
        # A Business Head / manager sees only their own subtree's employees;
        # Super Admin / HR / Finance see everyone.
        qs = super().get_queryset()
        from apps.accounts.access import is_admin_view, subordinate_user_ids
        role = getattr(getattr(self.request.user, "role", None), "name", "")
        if not (is_admin_view(self.request.user) or role in ("Finance", "HR")):
            qs = qs.filter(user_id__in=subordinate_user_ids(self.request.user, include_self=True))
        return qs

    @action(detail=True, methods=["get"])
    def ctc(self, request, pk=None):
        """Cost-To-Company breakdown for a month: salary + each cost category."""
        emp = self.get_object()
        today = timezone.localdate()
        month = int(request.query_params.get("month", today.month))
        year = int(request.query_params.get("year", today.year))
        lines = [{"label": "Salary", "amount": float(emp.salary or 0)}]
        rows = (EmployeeCost.objects.filter(employee=emp, month=month, year=year)
                .select_related("category"))
        for r in rows:
            lines.append({"label": r.category.name, "amount": float(r.amount)})
        total = sum(l["amount"] for l in lines)
        return Response({"employee": emp.user.name if emp.user else "—",
                         "month": month, "year": year, "lines": lines, "total_ctc": total})

    @action(detail=True, methods=["get"])
    def journey(self, request, pk=None):
        """Employee 360 relationship map — reporting line (up + down), the clients
        they own, their documents, and a timeline of their key events."""
        from django.db.models import Q, Sum
        from apps.crm.models import Customer
        from apps.sales.models import Revenue
        from .models import HRRequest, Leave, TrainingAssignment
        emp = self.get_object()
        user = emp.user

        # reporting line — up the manager chain, then direct reports
        up, m, seen = [], emp.manager, set()
        while m and m.id not in seen:
            seen.add(m.id)
            up.append({"id": m.id, "name": m.name, "role": getattr(getattr(m, "role", None), "name", "")})
            me = Employee.objects.select_related("manager").filter(user=m).first()
            m = me.manager if me else None
        reports = [{"emp_id": e.id, "name": e.user.name if e.user else "—",
                    "role": getattr(getattr(e.user, "role", None), "name", "")}
                   for e in Employee.objects.select_related("user", "user__role").filter(manager=user).exclude(user__is_superuser=True)]

        # clients / customers this person owns
        clients = []
        rev_by_cust = {}
        if user:
            for r in (Revenue.objects.filter(Q(customer__assigned_to=user) | Q(customer__lead__assigned_to=user))
                      .values("customer_id").annotate(s=Sum("net_revenue"))):
                rev_by_cust[r["customer_id"]] = float(r["s"] or 0)
            custs = (Customer.objects.filter(Q(assigned_to=user) | Q(lead__assigned_to=user)).distinct())
            for c in custs[:40]:
                clients.append({"id": c.id, "name": c.name,
                                "platform": ("DAGChain" if hasattr(c, "dagchain") else "FX Artha" if c.external_id else "CRM"),
                                "revenue": round(rev_by_cust.get(c.id, 0.0), 2)})
            clients.sort(key=lambda x: -x["revenue"])

        # timeline of key events
        events = []
        if emp.joining_date:
            events.append({"date": str(emp.joining_date), "kind": "join", "title": "Joined the company"})
        for lv in Leave.objects.filter(employee=emp).select_related("leave_type")[:30]:
            events.append({"date": str(lv.start_date or ""), "kind": "leave",
                           "title": f"{(lv.leave_type.leave_name if lv.leave_type else 'Leave')} — {lv.status}"})
        for rq in HRRequest.objects.filter(employee=emp)[:30]:
            events.append({"date": str(rq.created_at.date()), "kind": "request",
                           "title": f"{rq.get_request_type_display()} request '{rq.title}' — {rq.status}"})
        for ta in TrainingAssignment.objects.filter(employee=emp).select_related("module")[:30]:
            if ta.status == "completed":
                events.append({"date": str(getattr(ta, "completed_date", "") or ta.due_date or ""), "kind": "training",
                               "title": f"Completed training: {ta.module.title if ta.module_id else ''}"})
        events = [e for e in events if e["date"]]
        events.sort(key=lambda e: e["date"], reverse=True)

        return Response({
            "name": user.name if user else "—",
            "reporting": {"managers": up, "reports": reports},
            "clients": clients,
            "documents": {
                "photo": emp.photo.url if emp.photo else None,
                "document": emp.document.url if emp.document else None,
                "passport_expiry": emp.passport_expiry, "visa_expiry": emp.visa_expiry,
            },
            "timeline": events[:40],
        })


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("employee", "employee__user").exclude(employee__user__is_superuser=True)
    serializer_class = AttendanceSerializer
    filterset_fields = ["employee", "status", "date"]


class EmployeeActivityViewSet(viewsets.ModelViewSet):
    queryset = EmployeeActivity.objects.select_related("employee", "employee__user").exclude(employee__user__is_superuser=True)
    serializer_class = EmployeeActivitySerializer
    filterset_fields = ["employee", "date"]


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.select_related("employee", "employee__user", "leave_type").all()
    serializer_class = LeaveSerializer
    filterset_fields = ["employee", "status", "leave_type"]

    def get_queryset(self):
        qs = super().get_queryset().exclude(employee__user__is_superuser=True)
        user = self.request.user
        if can_manage_all_leaves(user):
            return qs  # HR / top management — everyone
        # Manager: own team's leaves + own. team = direct reports (User.manager).
        team_ids = list(User.objects.filter(manager=user).values_list("id", flat=True)) + [user.id]
        return qs.filter(employee__user_id__in=team_ids)

    def _can_approve(self, leave):
        user = self.request.user
        if can_manage_all_leaves(user):
            return True
        # A manager may approve only their direct reports' leaves.
        return leave.employee.user.manager_id == user.id

    def _decide(self, request, pk, new_status, verb):
        leave = self.get_object()
        if not self._can_approve(leave):
            return Response({"detail": "You can only approve your own team's leaves."},
                            status=status.HTTP_403_FORBIDDEN)
        leave.status = new_status
        leave.save(update_fields=["status"])
        notify(
            leave.employee.user,
            title=f"Leave {verb}",
            body=f"Your leave from {leave.start_date} to {leave.end_date} was {new_status} by {request.user.name}.",
            kind="success" if new_status == "approved" else "warning",
            link="/leaves-mine",
        )
        return Response(self.get_serializer(leave).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, pk, "approved", "approved")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, pk, "rejected", "rejected")


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.select_related("employee", "employee__user").exclude(employee__user__is_superuser=True)
    serializer_class = PayrollSerializer
    filterset_fields = ["employee", "month", "year"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate payslips for ALL active employees for a month (defaults to the
        just-ended month). Auto-runs on the 1st of each month; this lets HR trigger
        it on demand too. Idempotent — never overwrites an existing payslip."""
        from .services import generate_payroll
        today = timezone.localdate()
        pm = today.month - 1 or 12
        py = today.year if today.month > 1 else today.year - 1
        month = int(request.data.get("month") or pm)
        year = int(request.data.get("year") or py)
        created = generate_payroll(month, year)
        return Response({"month": month, "year": year, "created": created})

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """Auto-calculate a payroll draft for an employee/month/year.
        Basic = employee salary, Incentive = that month's computed incentives,
        Deduction = unpaid-leave days pro-rated, Final = basic + incentive + bonus − deduction.
        The Payroll form pre-fills from this when an employee is selected."""
        from django.db.models import Sum
        emp_id = request.query_params.get("employee")
        today = timezone.localdate()
        month = int(request.query_params.get("month") or today.month)
        year = int(request.query_params.get("year") or today.year)
        emp = Employee.objects.select_related("user").filter(id=emp_id).first()
        if not emp:
            return Response({"detail": "employee is required"}, status=400)

        basic = float(emp.salary or 0)
        incentive = float(Incentive.objects.filter(employee=emp, month=month, year=year)
                          .aggregate(t=Sum("amount"))["t"] or 0)
        # Unpaid leave deduction: approved "Unpaid" leave days × per-day salary (30-day month).
        deduction = 0.0
        unpaid_days = 0
        for lv in Leave.objects.filter(employee=emp, status="approved",
                                       leave_type__leave_name__icontains="unpaid"):
            if lv.start_date and lv.end_date and lv.start_date.month == month and lv.start_date.year == year:
                unpaid_days += (lv.end_date - lv.start_date).days + 1
        if unpaid_days:
            deduction = round(basic / 30.0 * unpaid_days, 2)
        bonus = 0.0
        return Response({
            "basic_salary": basic, "incentive": incentive, "bonus": bonus,
            "deduction": deduction, "unpaid_days": unpaid_days,
            # echo the period back so the form auto-fills month/year (defaults to
            # the current month/year) the moment an employee is selected.
            "month": month, "year": year,
            "final_salary": round(basic + incentive + bonus - deduction, 2),
        })

    @action(detail=True, methods=["get"])
    def payslip(self, request, pk=None):
        """Generate a downloadable PDF payslip."""
        import calendar
        import io

        from django.http import HttpResponse
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        p = self.get_object()
        emp = p.employee
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        brand = colors.HexColor("#4f46e5")

        # header band
        c.setFillColor(brand)
        c.rect(0, h - 35 * mm, w, 35 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(20 * mm, h - 20 * mm, "DAGOS")
        c.setFont("Helvetica", 11)
        c.drawString(20 * mm, h - 27 * mm, "Salary Payslip")
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(w - 20 * mm, h - 20 * mm,
                          f"{calendar.month_name[p.month]} {p.year}")

        # employee block
        y = h - 50 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Employee")
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#475569"))
        c.drawString(20 * mm, y - 6 * mm, f"Name: {emp.user.name}")
        c.drawString(20 * mm, y - 11 * mm, f"Employee ID: {emp.user.employee_id or '-'}")
        c.drawString(20 * mm, y - 16 * mm, f"Designation: {emp.designation or '-'}")

        # earnings / deductions table
        rows = [
            ("Basic Salary", p.basic_salary, ""),
            ("Incentive", p.incentive, ""),
            ("Bonus", p.bonus, ""),
            ("Deduction", "", p.deduction),
        ]
        ty = y - 30 * mm
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, ty, "Component")
        c.drawRightString(w - 70 * mm, ty, "Earnings")
        c.drawRightString(w - 20 * mm, ty, "Deductions")
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.line(20 * mm, ty - 2 * mm, w - 20 * mm, ty - 2 * mm)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#334155"))
        ry = ty - 9 * mm
        for label, earn, ded in rows:
            c.drawString(20 * mm, ry, label)
            if earn != "":
                c.drawRightString(w - 70 * mm, ry, f"${earn:,.2f}")
            if ded != "":
                c.drawRightString(w - 20 * mm, ry, f"${ded:,.2f}")
            ry -= 8 * mm

        # net pay box
        c.setFillColor(brand)
        c.roundRect(20 * mm, ry - 18 * mm, w - 40 * mm, 14 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(25 * mm, ry - 13 * mm, "NET PAY")
        c.drawRightString(w - 25 * mm, ry - 13 * mm, f"${p.final_salary:,.2f}")

        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, 15 * mm, "This is a system-generated payslip and does not require a signature.")
        c.showPage()
        c.save()
        buf.seek(0)
        resp = HttpResponse(buf, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="payslip_{emp.user.employee_id or emp.id}_{p.month}_{p.year}.pdf"'
        return resp


class IncentiveRuleViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = IncentiveRule.objects.select_related("business", "product").all()
    serializer_class = IncentiveRuleSerializer
    filterset_fields = ["business", "product", "formula_type"]


class TargetMultiplierViewSet(viewsets.ModelViewSet):
    queryset = TargetMultiplier.objects.select_related(
        "hierarchy_level", "employee", "employee__user").all()
    serializer_class = TargetMultiplierSerializer
    filterset_fields = ["scope", "hierarchy_level", "employee", "status"]


class PerformanceWeightViewSet(viewsets.ModelViewSet):
    queryset = PerformanceWeight.objects.select_related("hierarchy_level").all()
    serializer_class = PerformanceWeightSerializer
    filterset_fields = ["scope", "hierarchy_level", "status"]


class IncentiveSlabViewSet(viewsets.ModelViewSet):
    queryset = IncentiveSlab.objects.all()
    serializer_class = IncentiveSlabSerializer
    filterset_fields = ["basis", "status"]


class ActivityIncentiveViewSet(viewsets.ModelViewSet):
    queryset = ActivityIncentive.objects.select_related("metric").all()
    serializer_class = ActivityIncentiveSerializer
    filterset_fields = ["metric", "status"]


class FormulaRuleViewSet(viewsets.ModelViewSet):
    queryset = FormulaRule.objects.prefetch_related("conditions").all()
    serializer_class = FormulaRuleSerializer
    filterset_fields = ["status", "payout_type"]


class IncentiveViewSet(viewsets.ModelViewSet):
    queryset = Incentive.objects.select_related("employee", "employee__user", "rule").exclude(employee__user__is_superuser=True)
    serializer_class = IncentiveSerializer
    filterset_fields = ["employee", "month", "year"]

    @action(detail=False, methods=["post"])
    def calculate(self, request):
        """Auto-compute incentives from revenue for a month using IncentiveRules.

        Attribution: Revenue -> Customer -> originating Lead -> assigned RM (user)
        -> their Employee. Amount per business rule (percentage / fixed / slab).
        Result also flows into that month's Payroll incentive field.
        """
        from collections import defaultdict
        from decimal import Decimal

        from apps.sales.models import Revenue

        today = timezone.localdate()
        month = int(request.data.get("month") or today.month)
        year = int(request.data.get("year") or today.year)

        # one rule per business (first match)
        rules = {}
        for r in IncentiveRule.objects.all():
            rules.setdefault(r.business_id, r)

        revenues = (Revenue.objects
                    .filter(created_at__month=month, created_at__year=year)
                    .select_related("customer__lead__assigned_to", "business"))

        acc = defaultdict(Decimal)           # (employee_id, rule_id) -> amount
        emp_cache = {}
        skipped_no_owner = skipped_no_rule = 0

        for rev in revenues:
            lead = rev.customer.lead if rev.customer_id else None
            owner = lead.assigned_to if lead else None
            rule = rules.get(rev.business_id)
            if not owner:
                skipped_no_owner += 1
                continue
            if not rule:
                skipped_no_rule += 1
                continue
            if owner.id not in emp_cache:
                emp_cache[owner.id] = Employee.objects.filter(user=owner).first()
            emp = emp_cache[owner.id]
            if not emp:
                skipped_no_owner += 1
                continue

            net = rev.net_revenue or Decimal(0)
            if rule.formula_type in ("percentage", "slab"):
                amt = net * rule.formula_value / Decimal(100)
            elif rule.formula_type == "fixed":
                amt = rule.formula_value
            else:
                amt = Decimal(0)
            acc[(emp.id, rule.id)] += amt

        created = updated = 0
        per_employee = defaultdict(Decimal)
        for (emp_id, rule_id), amount in acc.items():
            amount = amount.quantize(Decimal("0.01"))
            _, was_created = Incentive.objects.update_or_create(
                employee_id=emp_id, rule_id=rule_id, source="manual", month=month, year=year,
                defaults={"amount": amount},
            )
            created += was_created
            updated += not was_created
            per_employee[emp_id] += amount

        # flow into payroll (if a payroll row exists for that employee/month)
        payrolls_updated = 0
        for emp_id, total in per_employee.items():
            pr = Payroll.objects.filter(employee_id=emp_id, month=month, year=year).first()
            if pr:
                pr.incentive = total.quantize(Decimal("0.01"))
                pr.save()  # save() recomputes final_salary
                payrolls_updated += 1

        return Response({
            "month": month, "year": year,
            "employees_credited": len(per_employee),
            "incentives_created": created,
            "incentives_updated": updated,
            "total_amount": float(sum(acc.values())),
            "payrolls_updated": payrolls_updated,
            "skipped_no_owner": skipped_no_owner,
            "skipped_no_rule": skipped_no_rule,
        })


# ---- Recruitment / ATS ----------------------------------------------------
class JobPostingViewSet(viewsets.ModelViewSet):
    from .serializers import JobPostingSerializer
    queryset = JobPosting.objects.select_related("business", "department").all()
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "business", "department"]
    search_fields = ["title", "role_name"]


class CandidateViewSet(viewsets.ModelViewSet):
    from .serializers import CandidateSerializer
    queryset = Candidate.objects.select_related("job").all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["job", "status"]
    search_fields = ["name", "email", "phone"]

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        cand = self.get_object()
        new = request.data.get("status")
        if new not in dict(Candidate.STATUS):
            return Response({"detail": "Invalid status."}, status=400)
        cand.status = new
        cand.save(update_fields=["status"])
        return Response(self.get_serializer(cand).data)

    @action(detail=True, methods=["post"])
    def rescore(self, request, pk=None):
        """Re-run the match after a job's required skills change."""
        from .recruitment import score_resume
        cand = self.get_object()
        pct, matched, missing = score_resume(cand.resume_text, cand.job.required_skills)
        cand.match_pct, cand.matched_skills, cand.missing_skills = pct, matched, missing
        if cand.status in ("applied", "shortlisted"):
            cand.status = "shortlisted" if pct >= cand.job.min_match_pct else "applied"
        cand.save()
        return Response(self.get_serializer(cand).data)


class PublicJobView(APIView):
    """Public job-ad page + application intake (no login). One shareable link
    per job (its public_token). POST parses the resume, scores it against the
    job's required skills, and auto-shortlists at/above the threshold."""
    permission_classes = [AllowAny]

    def _job(self, token):
        return JobPosting.objects.filter(public_token=token, status="open").first()

    def get(self, request, token):
        job = self._job(token)
        if not job:
            return Response({"detail": "This job is closed or the link is invalid."}, status=404)
        return Response({
            "title": job.title, "role_name": job.role_name,
            "business_name": job.business.name if job.business else "",
            "location": job.location, "experience": job.experience,
            "description": job.description,
        })

    def post(self, request, token):
        from .recruitment import extract_text, score_resume
        job = self._job(token)
        if not job:
            return Response({"detail": "This job is closed or the link is invalid."}, status=404)
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "Please enter your name."}, status=400)

        resume = request.FILES.get("resume")
        pasted = request.data.get("resume_text") or ""
        text = ((extract_text(resume) + "\n" + pasted) if resume else pasted).strip()
        pct, matched, missing = score_resume(text, job.required_skills)

        Candidate.objects.create(
            job=job, name=name,
            email=request.data.get("email", ""), phone=request.data.get("phone", ""),
            resume=resume, resume_text=text[:20000],
            match_pct=pct, matched_skills=matched, missing_skills=missing,
            status="shortlisted" if pct >= job.min_match_pct else "applied",
        )
        # candidates never see their score — just a confirmation
        return Response({"status": "received",
                         "message": f"Thanks {name}! Your application for {job.title} has been received."})


# ---- Training & Learning --------------------------------------------------
from .models import Assessment, TrainingAssignment, TrainingModule
from .serializers import (
    AssessmentSerializer, TrainingAssignmentSerializer, TrainingModuleSerializer,
)


class TrainingModuleViewSet(viewsets.ModelViewSet):
    queryset = TrainingModule.objects.select_related("owner__user").all()
    serializer_class = TrainingModuleSerializer
    filterset_fields = ["category", "mandatory", "active"]
    search_fields = ["module_id", "title", "category", "audience"]


class TrainingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = (TrainingAssignment.objects
                .select_related("employee__user", "module").all())
    serializer_class = TrainingAssignmentSerializer
    filterset_fields = ["employee", "module", "status"]
    search_fields = ["employee__user__name", "module__title", "module__module_id"]


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = (Assessment.objects
                .select_related("employee__user", "module", "assessor__user").all())
    serializer_class = AssessmentSerializer
    filterset_fields = ["employee", "module", "result"]
    search_fields = ["employee__user__name", "module__title", "certificate_id"]


class HRRequestViewSet(viewsets.ModelViewSet):
    """Self-service HR requests (visa / letter / reimbursement / …) with a
    multi-level approval chain. Scope: HR/admin see all; a manager sees their
    subtree; everyone else sees only their own. Approve/reject advance the chain."""
    from .models import HRRequest, HRRequestApproval
    from .serializers import HRRequestSerializer
    queryset = HRRequest.objects.select_related("employee__user").prefetch_related("approvals__approver").all()
    serializer_class = HRRequestSerializer
    filterset_fields = ["request_type", "status", "employee"]

    def get_queryset(self):
        from apps.accounts.access import is_admin_view, subordinate_user_ids
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(getattr(user, "role", None), "name", "")
        if is_admin_view(user) or role == "HR":
            return qs
        return qs.filter(employee__user_id__in=subordinate_user_ids(user, include_self=True))

    def perform_create(self, serializer):
        from .services import ensure_employee
        emp = ensure_employee(self.request.user)
        rtype = serializer.validated_data.get("request_type", "other")
        chain = []
        if emp and emp.manager_id:
            chain.append("manager")
        chain.append("hr")
        if rtype == "reimbursement":
            chain.append("head")            # money needs a higher sign-off
        serializer.save(employee=emp, chain=chain or ["hr"], stage_index=0, status="pending")

    def _decide(self, request, pk, decision):
        from .models import HRRequestApproval
        from .services import can_approve_stage
        req = self.get_object()
        if req.status != "pending":
            return Response({"detail": "This request is already closed."}, status=400)
        stage = req.current_stage
        if not can_approve_stage(request.user, req, stage):
            return Response({"detail": "You aren't the approver for this stage."}, status=403)
        HRRequestApproval.objects.create(request=req, stage=stage, approver=request.user,
                                         decision=decision, comment=request.data.get("comment", ""))
        if decision == "reject":
            req.status = "rejected"
            req.save(update_fields=["status"])
        else:
            req.stage_index += 1
            if req.stage_index >= len(req.chain or []):
                req.status = "approved"
            req.save(update_fields=["stage_index", "status"])
        if req.employee and req.employee.user_id:
            notify(req.employee.user, title=f"Request {req.status}",
                   body=f"Your {req.get_request_type_display()} request '{req.title}' is {req.status}.",
                   kind="info", link="/hr-requests")
        return Response(self.get_serializer(req).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, pk, "approve")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, pk, "reject")


# ==================================================================== HR SUITE
from .models import (
    Appraisal, EmployeeDocument, EmployeeEvent, EmployeeExit, HRTicket,
    PerformanceJournal, PIP, Policy, PolicyAcknowledgement, Recognition,
)
from .serializers import (
    AppraisalSerializer, EmployeeDocumentSerializer, EmployeeEventSerializer,
    EmployeeExitSerializer, HRTicketSerializer, PerformanceJournalSerializer,
    PIPSerializer, PolicySerializer, RecognitionSerializer,
)


def _is_hr(user):
    from apps.accounts.access import is_admin_view
    return is_admin_view(user) or getattr(getattr(user, "role", None), "name", "") == "HR"


def _scope_by_employee(qs, user, field="employee__user_id"):
    """HR/admin see all; everyone else only their own subtree (self + reports)."""
    if _is_hr(user):
        return qs
    from apps.accounts.access import subordinate_user_ids
    return qs.filter(**{f"{field}__in": subordinate_user_ids(user, include_self=True)})


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.select_related("employee__user").all()
    serializer_class = EmployeeDocumentSerializer
    filterset_fields = ["employee", "doc_type", "verified"]
    search_fields = ["title", "number", "employee__user__name"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)


class EmployeeEventViewSet(viewsets.ModelViewSet):
    queryset = EmployeeEvent.objects.select_related("employee__user").all()
    serializer_class = EmployeeEventSerializer
    filterset_fields = ["employee", "kind"]
    search_fields = ["title", "employee__user__name"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PerformanceJournalViewSet(viewsets.ModelViewSet):
    queryset = PerformanceJournal.objects.select_related("employee__user", "author").all()
    serializer_class = PerformanceJournalSerializer
    filterset_fields = ["employee", "kind"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AppraisalViewSet(viewsets.ModelViewSet):
    queryset = Appraisal.objects.select_related("employee__user").all()
    serializer_class = AppraisalSerializer
    filterset_fields = ["employee", "status", "period"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)


class PIPViewSet(viewsets.ModelViewSet):
    queryset = PIP.objects.select_related("employee__user", "owner").all()
    serializer_class = PIPSerializer
    filterset_fields = ["employee", "status"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class EmployeeExitViewSet(viewsets.ModelViewSet):
    queryset = EmployeeExit.objects.select_related("employee__user").all()
    serializer_class = EmployeeExitSerializer
    filterset_fields = ["employee", "status"]

    def get_queryset(self):
        return _scope_by_employee(super().get_queryset(), self.request.user)


class HRTicketViewSet(viewsets.ModelViewSet):
    """HR Helpdesk. Employees raise and see their own tickets; HR/admin see all
    and resolve. raised_by is always the caller."""
    queryset = HRTicket.objects.select_related("raised_by", "assigned_to").all()
    serializer_class = HRTicketSerializer
    filterset_fields = ["category", "status", "priority"]
    search_fields = ["subject", "raised_by__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if _is_hr(self.request.user):
            return qs
        return qs.filter(raised_by=self.request.user)

    def perform_create(self, serializer):
        ticket = serializer.save(raised_by=self.request.user)
        for u in User.objects.filter(role__name="HR", status="active"):
            notify(u, title="New HR ticket",
                   body=f"{self.request.user.name}: {ticket.subject}", kind="info", link="/hr-helpdesk")

    def update(self, request, *args, **kwargs):
        if not _is_hr(request.user) and self.get_object().raised_by_id != request.user.id:
            return Response({"detail": "Not allowed."}, status=403)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        if not _is_hr(request.user):
            return Response({"detail": "Only HR can resolve."}, status=403)
        t = self.get_object()
        t.status = "resolved"
        t.resolution = request.data.get("resolution", t.resolution)
        t.assigned_to = request.user
        t.save(update_fields=["status", "resolution", "assigned_to"])
        notify(t.raised_by, title="Ticket resolved",
               body=f"Your ticket '{t.subject}' was resolved.", kind="success", link="/hr-helpdesk")
        return Response(self.get_serializer(t).data)


class PolicyViewSet(viewsets.ModelViewSet):
    """Policy Centre. Everyone reads active policies; HR/admin manage them.
    acknowledge records a typed-name e-signature for the current version."""
    queryset = Policy.objects.prefetch_related("acks").all()
    serializer_class = PolicySerializer
    filterset_fields = ["category", "active"]
    search_fields = ["title"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if _is_hr(self.request.user) else qs.filter(active=True)

    def create(self, request, *args, **kwargs):
        if not _is_hr(request.user):
            return Response({"detail": "Only HR can add policies."}, status=403)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        policy = self.get_object()
        sig = (request.data.get("signature") or request.user.name or "").strip()
        if not sig:
            return Response({"detail": "Type your full name to sign."}, status=400)
        PolicyAcknowledgement.objects.get_or_create(
            policy=policy, user=request.user, version=policy.version,
            defaults={"signature": sig})
        return Response(self.get_serializer(policy).data)

    @action(detail=True, methods=["get"])
    def acks(self, request, pk=None):
        """Who has / has not signed - HR acceptance tracking."""
        policy = self.get_object()
        signed_ids = set(policy.acks.filter(version=policy.version).values_list("user_id", flat=True))
        rows = []
        for u in User.objects.filter(status="active").exclude(is_superuser=True):
            rows.append({"user": u.name, "signed": u.id in signed_ids})
        rows.sort(key=lambda r: (r["signed"], r["user"]))
        return Response({"version": policy.version,
                         "signed": len(signed_ids), "total": len(rows), "rows": rows})


class RecognitionViewSet(viewsets.ModelViewSet):
    """Recognition wall. Anyone nominates a peer; HR/admin approve. Everyone sees
    approved recognitions (the wall) plus their own pending nominations."""
    queryset = Recognition.objects.select_related("employee__user", "nominated_by").all()
    serializer_class = RecognitionSerializer
    filterset_fields = ["employee", "award", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        if _is_hr(self.request.user):
            return qs
        from django.db.models import Q
        return qs.filter(Q(status="approved") | Q(nominated_by=self.request.user))

    def perform_create(self, serializer):
        rec = serializer.save(nominated_by=self.request.user)
        for u in User.objects.filter(role__name="HR", status="active"):
            notify(u, title="New recognition nomination",
                   body=f"{self.request.user.name} nominated {rec.employee.user.name}", kind="info", link="/recognition")

    def _set_status(self, request, pk, new):
        if not _is_hr(request.user):
            return Response({"detail": "Only HR can moderate."}, status=403)
        rec = self.get_object()
        rec.status = new
        rec.save(update_fields=["status"])
        if new == "approved" and rec.employee and rec.employee.user_id:
            notify(rec.employee.user, title="You were recognised!",
                   body=f"{rec.get_award_display()}: {rec.reason[:120]}", kind="success", link="/recognition")
        return Response(self.get_serializer(rec).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set_status(request, pk, "approved")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set_status(request, pk, "rejected")
