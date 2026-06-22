from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import get_user_model

from apps.accounts.access import allowed_business_ids
from apps.crm.models import Business, Customer, Lead, LeadActivity, Opportunity, TargetAssignment
from apps.finance.models import Commission, Expense
from apps.hr.models import Attendance, Employee, Incentive, Leave, Payroll
from apps.sales.models import Revenue
from apps.support.models import Ticket

User = get_user_model()


def _money(qs, field):
    return qs.aggregate(t=Sum(field))["t"] or 0


def _scoped_revenue(user):
    qs = Revenue.objects.all()
    ids = allowed_business_ids(user)
    return qs.filter(business_id__in=ids) if ids is not None else qs


@api_view(["GET"])
def my_dashboard(request):
    """Personal KPIs scoped to the logged-in user."""
    user = request.user
    today = timezone.localdate()
    my_leads = Lead.objects.filter(assigned_to=user)
    my_opps = Opportunity.objects.filter(assigned_to=user)
    my_acts = LeadActivity.objects.filter(user=user)

    status_breakdown = list(
        my_leads.values("status").annotate(count=Count("id")).order_by("status")
    )
    recent = list(
        my_leads.order_by("-created_at")
        .values("id", "lead_code", "name", "status", "score")[:6]
    )
    followups = list(
        my_acts.filter(followup_date__gte=today)
        .select_related("lead")
        .order_by("followup_date")
        .values("id", "lead__name", "activity_type", "followup_date", "next_action")[:6]
    )
    my_revenue = Revenue.objects.filter(customer__lead__assigned_to=user)
    return Response({
        "my_leads": my_leads.count(),
        "my_new_leads": my_leads.filter(status="new").count(),
        "my_converted": my_leads.filter(status="converted").count(),
        "my_open_opportunities": my_opps.filter(status="open").count(),
        "my_won": my_opps.filter(stage="won").count(),
        "my_pipeline_value": _money(my_opps.filter(status="open"), "expected_revenue"),
        "my_revenue": _money(my_revenue, "net_revenue"),
        "my_gross_revenue": _money(my_revenue, "gross_revenue"),
        "my_activities_today": my_acts.filter(created_at__date=today).count(),
        "my_followups_due": my_acts.filter(followup_date__gte=today).count(),
        "my_targets": TargetAssignment.objects.filter(user=user).count(),
        "leads_by_status": status_breakdown,
        "recent_leads": recent,
        "upcoming_followups": followups,
    })


@api_view(["GET"])
def dashboard_summary(request):
    """High-level KPI cards for the main dashboard."""
    gross = _money(Revenue.objects.all(), "gross_revenue")
    net = _money(Revenue.objects.all(), "net_revenue")
    reps = []
    for u in User.objects.all():
        leads = Lead.objects.filter(assigned_to=u).count()
        if not leads:
            continue
        reps.append({
            "name": u.name,
            "role": getattr(u.role, "name", ""),
            "leads": leads,
            "won": Opportunity.objects.filter(assigned_to=u, stage="won").count(),
            "revenue": float(_money(Revenue.objects.filter(customer__lead__assigned_to=u), "net_revenue")),
        })
    reps.sort(key=lambda r: -r["revenue"])
    return Response({
        "top_reps": reps[:6],
        "total_leads": Lead.objects.count(),
        "new_leads": Lead.objects.filter(status="new").count(),
        "converted_leads": Lead.objects.filter(status="converted").count(),
        "total_customers": Customer.objects.count(),
        "open_opportunities": Opportunity.objects.filter(status="open").count(),
        "pipeline_value": _money(Opportunity.objects.filter(status="open"), "expected_revenue"),
        "gross_revenue": gross,
        "net_revenue": net,
        "open_tickets": Ticket.objects.exclude(status__in=["resolved", "closed"]).count(),
        "total_expenses": _money(Expense.objects.all(), "amount"),
        "total_commissions": _money(Commission.objects.all(), "amount"),
    })


@api_view(["GET"])
def team_dashboard(request):
    """Team Leader — data for the leader's direct reports."""
    team = User.objects.filter(manager=request.user)
    team_ids = list(team.values_list("id", flat=True)) + [request.user.id]
    leads = Lead.objects.filter(assigned_to_id__in=team_ids)
    opps = Opportunity.objects.filter(assigned_to_id__in=team_ids)
    members = [
        {
            "id": u.id, "name": u.name, "role": getattr(u.role, "name", ""),
            "leads": Lead.objects.filter(assigned_to=u).count(),
            "won": Opportunity.objects.filter(assigned_to=u, stage="won").count(),
        }
        for u in team
    ]
    return Response({
        "team_size": team.count(),
        "team_leads": leads.count(),
        "team_converted": leads.filter(status="converted").count(),
        "team_open_opportunities": opps.filter(status="open").count(),
        "team_pipeline": _money(opps.filter(status="open"), "expected_revenue"),
        "team_followups": LeadActivity.objects.filter(user_id__in=team_ids).count(),
        "leads_by_status": list(leads.values("status").annotate(count=Count("id")).order_by("status")),
        "members": members,
    })


@api_view(["GET"])
def hr_dashboard(request):
    """HR — people, attendance, leaves, payroll, incentives."""
    today = timezone.localdate()
    month = today.month
    year = today.year
    return Response({
        "total_employees": Employee.objects.count(),
        "present_today": Attendance.objects.filter(date=today, status="present").count(),
        "on_leave_today": Attendance.objects.filter(date=today, status="leave").count(),
        "pending_leaves": Leave.objects.filter(status="pending").count(),
        "payroll_this_month": _money(Payroll.objects.filter(month=month, year=year), "final_salary"),
        "incentives_this_month": _money(Incentive.objects.filter(month=month, year=year), "amount"),
        "leaves_by_status": list(Leave.objects.values("status").annotate(count=Count("id"))),
        "headcount_by_dept": list(
            Employee.objects.values("department__department_name").annotate(count=Count("id")).order_by("-count")
        ),
    })


@api_view(["GET"])
def finance_dashboard(request):
    """Finance — revenue, expenses, commissions, profit."""
    today = timezone.localdate()
    rev = _scoped_revenue(request.user)
    gross = _money(rev, "gross_revenue")
    net = _money(rev, "net_revenue")
    expenses = _money(Expense.objects.all(), "amount")
    commissions = _money(Commission.objects.all(), "amount")
    payroll = _money(Payroll.objects.filter(month=today.month, year=today.year), "final_salary")
    profit = float(net) - float(expenses) - float(commissions) - float(payroll)
    return Response({
        "gross_revenue": gross,
        "net_revenue": net,
        "total_expenses": expenses,
        "total_commissions": commissions,
        "payroll_this_month": payroll,
        "profit": profit,
        "revenue_by_business": [
            {"business": d["business__name"] or "Unknown", "net": d["net"] or 0}
            for d in rev.values("business__name").annotate(net=Sum("net_revenue")).order_by("-net")
        ],
        "expenses_by_type": list(
            Expense.objects.values("expense_type").annotate(total=Sum("amount")).order_by("-total")
        ),
    })


@api_view(["GET"])
def support_dashboard(request):
    """Support — ticket queue health."""
    tickets = Ticket.objects.all()
    return Response({
        "total_tickets": tickets.count(),
        "open_tickets": tickets.exclude(status__in=["resolved", "closed"]).count(),
        "resolved_tickets": tickets.filter(status="resolved").count(),
        "urgent_tickets": tickets.filter(priority="urgent").exclude(status__in=["resolved", "closed"]).count(),
        "by_status": list(tickets.values("status").annotate(count=Count("id")).order_by("status")),
        "by_priority": list(tickets.values("priority").annotate(count=Count("id")).order_by("priority")),
    })


@api_view(["GET"])
def sales_dashboard(request):
    """Sales Manager — company-wide sales (no HR/finance)."""
    from apps.crm.models import Target
    from apps.crm.serializers import TargetSerializer

    rev = _scoped_revenue(request.user)
    targets = TargetSerializer(Target.objects.all().order_by("end_date")[:6], many=True).data
    return Response({
        "targets": targets,
        "total_leads": Lead.objects.count(),
        "converted_leads": Lead.objects.filter(status="converted").count(),
        "open_opportunities": Opportunity.objects.filter(status="open").count(),
        "pipeline_value": _money(Opportunity.objects.filter(status="open"), "expected_revenue"),
        "won_deals": Opportunity.objects.filter(stage="won").count(),
        "net_revenue": _money(rev, "net_revenue"),
        "by_stage": list(Opportunity.objects.values("stage").annotate(count=Count("id"), value=Sum("expected_revenue")).order_by("stage")),
        "leads_by_source": [
            {"source": d["source__name"] or "Unknown", "count": d["count"]}
            for d in Lead.objects.values("source__name").annotate(count=Count("id")).order_by("-count")
        ],
        "top_reps": [
            {"name": u.name, "leads": Lead.objects.filter(assigned_to=u).count(),
             "won": Opportunity.objects.filter(assigned_to=u, stage="won").count()}
            for u in User.objects.all()[:8]
        ],
    })


@api_view(["GET"])
def leads_by_status(request):
    data = Lead.objects.values("status").annotate(count=Count("id")).order_by("status")
    return Response(list(data))


@api_view(["GET"])
def leads_by_source(request):
    data = (Lead.objects.values("source__name")
            .annotate(count=Count("id")).order_by("-count"))
    return Response([{"source": d["source__name"] or "Unknown", "count": d["count"]} for d in data])


@api_view(["GET"])
def opportunities_by_stage(request):
    data = (Opportunity.objects.values("stage")
            .annotate(count=Count("id"), value=Sum("expected_revenue")).order_by("stage"))
    return Response(list(data))


@api_view(["GET"])
def revenue_by_business(request):
    data = (Revenue.objects.values("business__name")
            .annotate(gross=Sum("gross_revenue"), net=Sum("net_revenue")).order_by("-gross"))
    return Response([{"business": d["business__name"] or "Unknown",
                      "gross": d["gross"] or 0, "net": d["net"] or 0} for d in data])


@api_view(["GET"])
def revenue_trend(request):
    """Monthly net revenue trend."""
    data = (Revenue.objects.annotate(month=TruncMonth("created_at"))
            .values("month").annotate(net=Sum("net_revenue")).order_by("month"))
    return Response([{"month": d["month"].strftime("%b %Y") if d["month"] else "",
                      "net": d["net"] or 0} for d in data])
