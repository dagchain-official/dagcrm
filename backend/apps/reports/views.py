from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .assistant import answer_question
from .aum import compute_aum, scoped_aum
from .contribution import compute_contribution, scoped_contribution
from .formulas import compute_formulas, run_formulas, scoped_formulas, variable_options
from .incentives import compute_incentives, run_incentives, scoped_incentives
from .metrics import compute_kpis, scoped_kpis
from .performance import compute_performance, scoped_performance
from .pnl import compute_pnl, scoped_for
from .targets import compute_targets, scoped_targets

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


@api_view(["POST"])
def ai_ask(request):
    """Natural-language Q&A over the live CRM database (role-scoped)."""
    question = (request.data or {}).get("message", "")
    return Response({"reply": answer_question(request.user, question)})


@api_view(["GET"])
def pnl(request):
    """P&L per hierarchy level (Revenue − Cost), rolled up the org tree."""
    user = request.user
    role = getattr(getattr(user, "role", None), "name", "")
    if role == "Sales Executive":      # cost/P&L is not exposed to RMs
        return Response({"detail": "P&L is available to managers, Finance and admins."}, status=403)
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_for(user, compute_pnl(month, year)))


@api_view(["GET"])
def target_board(request):
    """CTC-based targets (Target = CTC × multiplier), rolled up the org tree.
    A manager sees their team's rolled-up target; an RM sees their own."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_targets(user, compute_targets(month, year)))


@api_view(["GET"])
def kpi_board(request):
    """Configurable KPIs (PART 6) per employee, rolled up the org tree.
    Optional ?business= filter. Aggregation-aware (sum/count/avg/latest)."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    business = request.query_params.get("business")
    business_id = int(business) if business else None
    return Response(scoped_kpis(user, compute_kpis(month, year, business_id)))


@api_view(["GET"])
def business_dashboard(request):
    """Per-business dashboard — revenue + configurable KPIs (PART 6) + AUM +
    top RMs for one business. Cards are driven by that business's metrics, so
    nothing is hardcoded per business."""
    biz = Business.objects.filter(id=request.query_params.get("business")).first()
    if not biz:
        return Response({"detail": "Business not found."}, status=404)
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))

    rev = Revenue.objects.filter(business=biz)
    month_rev = rev.filter(created_at__year=year, created_at__month=month)

    trend = list(rev.annotate(m=TruncMonth("created_at")).values("m")
                 .annotate(net=Sum("net_revenue")).order_by("m"))
    trend = [{"month": t["m"].strftime("%b %Y") if t["m"] else "", "net": float(t["net"] or 0)}
             for t in trend][-6:]

    # KPI cards = this business's OWN metrics (drop cross-business globals)
    kpi = compute_kpis(month, year, business_id=biz.id)
    kpi_cards = [{"name": m["name"], "unit": m["unit"], "category": m["category"],
                  "value": kpi["company"].get(m["id"], 0)}
                 for m in kpi["metrics"] if m["business"] == biz.name]

    aum = compute_aum(month, year, business_id=biz.id)["company"]
    has_aum = any(aum.get(k) for k in ("existing", "new_deposits", "withdrawals", "closing"))

    rows = (rev.values("customer__lead__assigned_to")
            .annotate(net=Sum("net_revenue")).order_by("-net"))
    names = dict(User.objects.values_list("id", "name"))
    top_reps = [{"name": names.get(r["customer__lead__assigned_to"], "—"),
                 "revenue": float(r["net"] or 0)}
                for r in rows if r["customer__lead__assigned_to"]][:6]

    return Response({
        "business": {"id": biz.id, "name": biz.name},
        "month": month, "year": year,
        "gross_revenue": _money(rev, "gross_revenue"),
        "net_revenue": _money(rev, "net_revenue"),
        "month_net_revenue": _money(month_rev, "net_revenue"),
        "customers": Customer.objects.filter(revenues__business=biz).distinct().count(),
        "revenue_trend": trend,
        "kpis": kpi_cards,
        "aum": aum if has_aum else None,
        "top_reps": top_reps,
    })


@api_view(["GET"])
def performance(request):
    """3-scorecard performance (Revenue / Growth / Activity) with admin weightage."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_performance(user, compute_performance(month, year)))


@api_view(["GET"])
def incentive_board(request):
    """Preview computed incentives (slab + activity) per employee — no writes."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_incentives(user, compute_incentives(month, year)))


@api_view(["POST"])
def incentive_run(request):
    """Persist incentives into Incentive + Payroll (admins / Finance / HR only)."""
    from apps.accounts.access import is_admin_view
    user = request.user
    role = getattr(getattr(user, "role", None), "name", "")
    if not (is_admin_view(user) or role in ("Finance", "HR")):
        return Response({"detail": "Only admins, Finance or HR can run incentives."}, status=403)
    today = timezone.localdate()
    month = int((request.data or {}).get("month") or today.month)
    year = int((request.data or {}).get("year") or today.year)
    return Response(run_incentives(month, year))


@api_view(["GET"])
def aum_board(request):
    """New AUM (Existing / New Deposits / Withdrawals / Net New) rolled up the tree."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_aum(user, compute_aum(month, year)))


@api_view(["GET"])
def contribution_board(request):
    """Net Business Contribution (admin-weighted components) rolled up the tree."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_contribution(user, compute_contribution(month, year)))


@api_view(["GET"])
def formula_variables(request):
    """Variables an admin can reference in formula conditions/payouts."""
    return Response({"variables": variable_options()})


@api_view(["GET"])
def formula_board(request):
    """Preview formula-rule payouts per employee (which rules fired) — no writes."""
    user = request.user
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    return Response(scoped_formulas(user, compute_formulas(month, year)))


@api_view(["POST"])
def formula_run(request):
    """Persist formula payouts into Incentive + Payroll (admins / Finance / HR)."""
    from apps.accounts.access import is_admin_view
    user = request.user
    role = getattr(getattr(user, "role", None), "name", "")
    if not (is_admin_view(user) or role in ("Finance", "HR")):
        return Response({"detail": "Only admins, Finance or HR can run payouts."}, status=403)
    today = timezone.localdate()
    month = int((request.data or {}).get("month") or today.month)
    year = int((request.data or {}).get("year") or today.year)
    return Response(run_formulas(month, year))
