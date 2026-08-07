from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from apps.accounts.api_permissions import module_required
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
from .traders import compute_traders_lots, scoped_traders_lots
from .fxartha import compute_fxartha_traders, fxartha_account_detail, scoped_fxartha_traders

from django.contrib.auth import get_user_model

from apps.accounts.access import allowed_business_ids
from apps.crm.models import Business, Customer, Lead, LeadActivity, Opportunity, TargetAssignment
from apps.finance.models import Commission, Expense
from apps.hr.models import Attendance, Employee, Incentive, Leave, Payroll
from apps.sales.models import Revenue
from apps.support.models import Ticket

User = get_user_model()


# every call-like activity type counts toward a "Calls" figure
CALL_TYPES = ["call", "outbound_call", "inbound_call", "callback"]


def _training_stats(emp_ids=None):
    """Training compliance + assessment pass rate for a set of employees (all if
    None). Compliance = completed / (assigned that aren't exempted). Overdue =
    not-done assignments past their due date."""
    from apps.hr.models import Assessment, TrainingAssignment
    ta = TrainingAssignment.objects.all()
    ass = Assessment.objects.all()
    if emp_ids is not None:
        ta = ta.filter(employee_id__in=emp_ids)
        ass = ass.filter(employee_id__in=emp_ids)
    counted = ta.exclude(status="exempted")
    total = counted.count()
    completed = counted.filter(status="completed").count()
    today = timezone.localdate()
    overdue = counted.exclude(status="completed").filter(due_date__lt=today).count()
    passed = ass.filter(result="pass").count()
    ass_total = ass.count()
    return {
        "compliance": round(completed / total, 4) if total else 0.0,
        "pass_rate": round(passed / ass_total, 4) if ass_total else 0.0,
        "overdue": overdue,
        "assignments": total,
    }


def _money(qs, field):
    return qs.aggregate(t=Sum(field))["t"] or 0


def _scoped_revenue(user):
    qs = Revenue.objects.all()
    ids = allowed_business_ids(user)
    return qs.filter(business_id__in=ids) if ids is not None else qs


def kpi_scorecard(user_ids, month=None, year=None):
    """The sales-department scorecard for a set of users — the same 10 fields on
    every role's dashboard, only the scope changes: one RM for the exec dashboard,
    a team for the leader/manager, everyone for admin. Defaults to the current
    month; pass month/year to view any month.

    All real data. Talk Time / Training aren't CRM metrics yet, so they read a
    same-named manual metric if one exists (0 otherwise) — add the metric and the
    tile fills in with no code change.
    """
    from apps.crm.models import MetricDefinition, MetricEntry

    from .incentives import compute_incentives
    from .pnl import _revenue_by_user

    today = timezone.localdate()
    m, y = int(month or today.month), int(year or today.year)
    uids = set(u for u in user_ids if u)
    leads = Lead.objects.pipeline().filter(assigned_to_id__in=uids,
                                           created_at__year=y, created_at__month=m)
    acts = LeadActivity.objects.filter(lead__assigned_to_id__in=uids,
                                       created_at__year=y, created_at__month=m)
    by_user, _ = _revenue_by_user(m, y)
    revenue = round(sum(float(by_user.get(u, 0)) for u in uids), 2)

    emp_ids = set(Employee.objects.filter(user_id__in=uids).values_list("id", flat=True))

    def metric_sum(name):
        mid = (MetricDefinition.objects.filter(name__iexact=name, status="active")
               .values_list("id", flat=True).first())
        if not mid or not emp_ids:
            return 0.0
        return float(MetricEntry.objects.filter(metric_id=mid, employee_id__in=emp_ids,
                                                date__year=y, date__month=m)
                     .aggregate(s=Sum("value"))["s"] or 0)

    inc = [r for r in compute_incentives(m, y)["rows"] if r["id"] in emp_ids]
    tot_target = sum(r["target"] for r in inc)
    overall = round(sum(r["revenue"] for r in inc) / tot_target, 4) if tot_target else 0.0
    earned = round(sum(r["total"] for r in inc), 2)
    paid = float(Payroll.objects.filter(month=m, year=y, employee_id__in=emp_ids)
                 .aggregate(s=Sum("incentive"))["s"] or 0)

    # --- Quality Score: connect rate + meeting-completion rate, from real activity
    calls_qs = acts.filter(activity_type__in=CALL_TYPES)
    n_calls = calls_qs.count()
    connected = calls_qs.exclude(outcome="").exclude(
        outcome__in=["no_answer", "busy", "voicemail", "wrong_number"]).count()
    n_booked = acts.exclude(meeting_status="").count()
    n_done = acts.filter(meeting_status="completed").count()
    parts = []
    if n_calls:
        parts.append(connected / n_calls)
    if n_booked:
        parts.append(n_done / n_booked)
    quality = round(sum(parts) / len(parts), 4) if parts else 0.0

    # --- Follow-up compliance: of the follow-ups that fell due, how many were
    # honoured (the rep logged another activity on that lead by the due date).
    from collections import defaultdict
    due_fu = list(acts.exclude(followup_date=None).filter(followup_date__lt=today)
                  .values_list("lead_id", "created_at", "followup_date"))
    followup_compliance = 0.0
    if due_fu:
        lead_ids = {x[0] for x in due_fu}
        by_lead = defaultdict(list)
        for lid, ca in LeadActivity.objects.filter(lead_id__in=lead_ids).values_list("lead_id", "created_at"):
            by_lead[lid].append(ca)
        honored = sum(1 for lid, created, due in due_fu
                      if any(ca > created and ca.date() <= due for ca in by_lead[lid]))
        followup_compliance = round(honored / len(due_fu), 4)

    # --- Attendance %: present-equivalent (half-day = 0.5) over days recorded
    att = Attendance.objects.filter(employee_id__in=emp_ids, date__year=y, date__month=m)
    att_total = att.count()
    present_eq = att.filter(status="present").count() + 0.5 * att.filter(status="half_day").count()
    attendance = round(present_eq / att_total, 4) if att_total else 0.0

    # --- Agent-KPI ratios & splits (from the same activity set)
    n_leads = leads.count()
    contacted = leads.exclude(status__in=["new", "assigned"]).count()   # got at least attempted
    contact_rate = round(contacted / n_leads, 4) if n_leads else 0.0
    connect_rate = round(connected / n_calls, 4) if n_calls else 0.0
    total_talk = float(calls_qs.aggregate(s=Sum("duration_min"))["s"] or 0)
    avg_talk = round(total_talk / n_calls, 2) if n_calls else 0.0
    talk_time = total_talk or metric_sum("Talk Time")   # real call minutes, else a manual metric
    callbacks_due = acts.filter(outcome="callback").count()       # a callback was requested
    callbacks_completed = acts.filter(activity_type="callback").count()   # a callback was made

    return {
        "leads": n_leads,
        "calls": n_calls,
        "talk_time": round(talk_time, 2),
        "meetings": acts.filter(activity_type="meeting").count(),
        "sales": leads.filter(status="converted").count(),
        "revenue": revenue,
        "overall_kpi": overall,
        "incentive_earned": earned,
        "incentive_paid": round(paid, 2),
        # training compliance for these people (0..1) — the Training tile
        "training": _training_stats(emp_ids)["compliance"],
        "quality_score": quality,               # connect + meeting-completion blend
        "followup_compliance": followup_compliance,
        "attendance": attendance,
        # Agent KPI ratios / splits (Business Life Monitor)
        "contacted": contacted,
        "contact_rate": contact_rate,
        "connect_rate": connect_rate,
        "avg_talk_min": avg_talk,
        "callbacks_due": callbacks_due,
        "callbacks_completed": callbacks_completed,
        "meetings_booked": n_booked,
        "meetings_done": n_done,
    }


@api_view(["GET"])
def kpi_scorecard_month(request):
    """The dashboard KPI scorecard for a chosen month — scope 'self' (the caller),
    'team' (their subtree), or 'company' (everyone). Powers the month picker on the
    'My KPIs' card so any month can be viewed, not just the current one."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    today = timezone.localdate()
    month = int(request.query_params.get("month") or today.month)
    year = int(request.query_params.get("year") or today.year)
    scope = request.query_params.get("scope", "self")
    user = request.user
    role = getattr(getattr(user, "role", None), "name", "")
    sees_all = is_admin_view(user) or role in ("Finance", "HR")
    target = request.query_params.get("user")
    if target and target.isdigit():
        tid = int(target)
        uids = [tid] if (sees_all or tid in subordinate_user_ids(user, include_self=True)) else [user.id]
    elif scope == "company" and sees_all:
        uids = list(User.objects.values_list("id", flat=True))
    elif scope == "team":
        uids = list(subordinate_user_ids(user, include_self=True))
    else:
        uids = [user.id]
    return Response({"kpis": kpi_scorecard(uids, month, year), "month": month, "year": year})


def _fxartha_dashboard():
    """The last-synced FXArtha platform dashboard. Its revenue figures are
    authoritative: our per-trader rows carry commission only (no swap) and are
    dated by sync time, so summing them both understates the platform total and
    piles its whole history onto one month."""
    from apps.integrations.models import IntegrationConnection
    conn = IntegrationConnection.objects.filter(platform="fxartha").first()
    return ((conn.config or {}).get("dashboard") or {}) if conn else {}


@api_view(["GET"])
def my_dashboard(request):
    """Personal KPIs scoped to the logged-in user. An admin/manager may pass
    ?user=<id> to view another employee's dashboard (only within their reach)."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    user = request.user
    target = request.query_params.get("user")
    if target and str(target) != str(user.id):
        try:
            tid = int(target)
        except (TypeError, ValueError):
            tid = None
        if tid and (is_admin_view(user) or tid in subordinate_user_ids(user, include_self=True)):
            user = User.objects.filter(id=tid, is_superuser=False).first() or user
    today = timezone.localdate()
    my_leads = Lead.objects.pipeline().filter(assigned_to=user)
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
    # ramped sales target — 6x CTC month 1, 8x month 2, 10x month 3+
    from apps.hr.models import Employee
    _emp = Employee.objects.filter(user=user).first()
    _mult = ramped_multiplier(_emp, today) if _emp else 10
    _ctc = float(_emp.monthly_ctc(today.month, today.year)) if _emp else 0.0
    _rev_val = float(_money(my_revenue, "net_revenue") or 0)
    _target = round(_ctc * _mult, 2)
    return Response({
        "my_target": _target,
        "my_target_multiplier": _mult,
        "my_ctc": round(_ctc, 2),
        "my_target_pct": round(_rev_val / _target * 100, 1) if _target else 0.0,
        "my_leads": my_leads.active().count(),   # active only
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
        "kpis": kpi_scorecard([user.id]),
        "user_name": user.name,
    })


@api_view(["GET"])
def dashboard_summary(request):
    """High-level KPI cards for the main dashboard."""
    # FXArtha reports its own platform revenue — take it as-is and drop only its
    # per-trader rows so they aren't double-counted. Every other source still
    # counts: the CRM's own revenue and other integrations (e.g. DAGChain nodes).
    fx_revenue = float(_fxartha_dashboard().get("total_revenue") or 0)
    other_revenue = Revenue.objects.exclude(external_id__startswith="fxa")
    gross = float(_money(other_revenue, "gross_revenue")) + fx_revenue
    net = float(_money(other_revenue, "net_revenue")) + fx_revenue
    reps = []
    for u in User.objects.all():
        u_leads = Lead.objects.pipeline().filter(assigned_to=u)
        if not u_leads.exists():
            continue
        reps.append({
            "name": u.name,
            "role": getattr(u.role, "name", ""),
            "leads": u_leads.active().count(),   # active only
            "won": Opportunity.objects.filter(assigned_to=u, stage="won").count(),
            "revenue": float(_money(Revenue.objects.filter(customer__lead__assigned_to=u), "net_revenue")),
        })
    reps.sort(key=lambda r: -r["revenue"])
    return Response({
        "top_reps": reps[:6],
        "kpis": kpi_scorecard(User.objects.values_list("id", flat=True)),
        "total_leads": Lead.objects.pipeline().active().count(),   # active only
        "new_leads": Lead.objects.pipeline().filter(status="new").count(),
        "converted_leads": Lead.objects.pipeline().filter(status="converted").count(),
        "total_customers": Customer.objects.pipeline().count(),
        "open_opportunities": Opportunity.objects.filter(status="open").count(),
        "pipeline_value": _money(Opportunity.objects.filter(status="open"), "expected_revenue"),
        "gross_revenue": gross,
        "net_revenue": net,
        "open_tickets": Ticket.objects.exclude(status__in=["resolved", "closed"]).count(),
        "total_expenses": _money(Expense.objects.all(), "amount"),
        "total_commissions": _money(Commission.objects.all(), "amount"),
    })


def _health_status(score):
    """Bands relative to the configured company-health target: at/above target =
    Healthy, within 25 points below = Watch, lower = Critical."""
    from apps.accounts.models import CompanySettings
    target = float(CompanySettings.get_solo().company_health_target or 0.85)
    if score >= target:
        return "Healthy"
    if score >= target - 0.25:
        return "Watch"
    return "Critical"


@api_view(["GET", "PUT"])
def company_settings(request):
    """Company-wide settings (the Excel Settings list). Anyone signed in may read
    them; only an admin view may change them."""
    from apps.accounts.access import is_admin_view
    from apps.accounts.models import CompanySettings
    cfg = CompanySettings.get_solo()
    can_edit = is_admin_view(request.user)
    if request.method == "PUT":
        if not can_edit:
            return Response({"detail": "Only administrators can change settings."}, status=403)
        num = {"workdays_per_month": int, "default_incentive_rate": float,
               "training_pass_mark": float, "first_contact_sla_min": int,
               "company_health_target": float}
        for field, cast in num.items():
            if field in request.data and request.data[field] not in (None, ""):
                try:
                    setattr(cfg, field, cast(request.data[field]))
                except (TypeError, ValueError):
                    return Response({field: "Must be a number."}, status=400)
        if request.data.get("currency"):
            cfg.currency = str(request.data["currency"]).upper()[:8]
        cfg.save()
    return Response({
        "currency": cfg.currency,
        "workdays_per_month": cfg.workdays_per_month,
        "default_incentive_rate": float(cfg.default_incentive_rate),
        "training_pass_mark": float(cfg.training_pass_mark),
        "first_contact_sla_min": cfg.first_contact_sla_min,
        "company_health_target": float(cfg.company_health_target),
        "can_edit": can_edit,
    })


@api_view(["GET"])
def company_health(request):
    """CEO Command Center — the company-health view: headline numbers plus a
    five-dimension health index (Sales / Execution / Learning / Customer /
    Finance -> Overall), mirroring the Excel monitor.

    Real where the data exists. Learning depends on a Training/Assessment module
    the CRM doesn't have yet, so Training Compliance / Assessment Pass Rate and
    the Learning dimension read 0 until that module is built.
    """
    today = timezone.localdate()
    m, y = today.month, today.year
    # Super Admin sees the whole company; a Business Head (or any manager) sees
    # only their own subtree — same scoping rule as everywhere else, so a BH's
    # deals/leads/revenue are their team's, not another team's.
    from django.db.models import Q
    from apps.accounts.access import subordinate_user_ids
    full = request.user.is_superuser or getattr(getattr(request.user, "role", None), "name", "") == "Super Admin"
    sub = None if full else subordinate_user_ids(request.user, include_self=True)

    leads = Lead.objects.pipeline() if full else Lead.objects.pipeline().filter(assigned_to_id__in=sub)
    opps = Opportunity.objects.all() if full else Opportunity.objects.filter(assigned_to_id__in=sub)
    fu = LeadActivity.objects.all() if full else LeadActivity.objects.filter(lead__assigned_to_id__in=sub)

    total_leads = leads.count()
    won = leads.filter(status="converted").count()
    lost = leads.filter(status="lost").count()
    closed_won = opps.filter(stage="won").count() or won

    if full:
        fx_revenue = float(_fxartha_dashboard().get("total_revenue") or 0)
        revenue = float(_money(Revenue.objects.exclude(external_id__startswith="fxa"), "net_revenue")) + fx_revenue
    else:
        # revenue attributed to the subtree's own customers (customer owner, else
        # the originating lead's RM) — includes their FX/DAGChain rows.
        revenue = float(_money(
            Revenue.objects.filter(Q(customer__assigned_to_id__in=sub) | Q(customer__lead__assigned_to_id__in=sub)),
            "net_revenue"))
    gross_profit = round(revenue, 2)                       # net = after commission
    expenses = float(_money(Expense.objects.all(), "amount"))
    weighted_pipeline = float(_money(opps.filter(status="open"), "expected_revenue"))
    overdue_actions = fu.filter(followup_date__lt=today).count()

    # ---- five health dimensions (0..1) ----
    tgt = compute_targets(m, y).get("company", {})
    if full and tgt.get("target"):
        sales = min(1.0, tgt.get("achieved", 0) / tgt["target"])
    else:
        sales = (won / total_leads) if total_leads else 0.0

    total_fu = fu.filter(followup_date__isnull=False).count()
    # no follow-ups logged yet = no execution data → 0 (not a misleading 100%)
    execution = (1 - overdue_actions / total_fu) if total_fu else 0.0

    tstats = _training_stats()
    training_compliance = tstats["compliance"]
    assessment_pass_rate = tstats["pass_rate"]
    learning = training_compliance

    # Customer health proxy: share of customers that actually generate revenue
    cust_qs = (Customer.objects.all() if full
               else Customer.objects.filter(Q(assigned_to_id__in=sub) | Q(lead__assigned_to_id__in=sub)))
    total_custs = cust_qs.exclude(external_id="").count() or cust_qs.count()
    active_custs = cust_qs.filter(revenues__isnull=False).distinct().count()
    customer = (active_custs / total_custs) if total_custs else 0.0

    finance = max(0.0, min(1.0, (revenue - expenses) / revenue)) if revenue else 0.0

    dims = [
        ("Sales", sales), ("Execution", execution), ("Learning", learning),
        ("Customer", customer), ("Finance", finance),
    ]
    overall = sum(s for _, s in dims) / len(dims)
    health = [{"dimension": d, "score": round(s, 4), "status": _health_status(s)}
              for d, s in dims]
    health.append({"dimension": "Overall", "score": round(overall, 4),
                   "status": _health_status(overall)})

    return Response({
        "total_leads": leads.active().count(),   # 'Active Leads' tile — only leads still in the Leads section
        "closed_won": closed_won,
        "revenue": round(revenue, 2),
        "gross_profit": gross_profit,
        "weighted_pipeline": round(weighted_pipeline, 2),
        "overdue_actions": overdue_actions,
        "training_compliance": training_compliance,
        "assessment_pass_rate": assessment_pass_rate,
        "health": health,
    })


@api_view(["GET"])
def team_dashboard(request):
    """Team Leader — data for the leader's direct reports. An admin/manager may
    pass ?user=<leader id> to view that leader's team (within their reach)."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    leader = request.user
    target = request.query_params.get("user")
    if target and str(target) != str(leader.id):
        try:
            tid = int(target)
        except (TypeError, ValueError):
            tid = None
        if tid and (is_admin_view(leader) or tid in subordinate_user_ids(leader, include_self=True)):
            leader = User.objects.filter(id=tid, is_superuser=False).first() or leader
    team = User.objects.filter(manager=leader)
    team_ids = list(team.values_list("id", flat=True)) + [leader.id]
    leads = Lead.objects.pipeline().filter(assigned_to_id__in=team_ids)
    opps = Opportunity.objects.filter(assigned_to_id__in=team_ids)

    # per-agent scorecard (this month): KPI (attainment), revenue, calls,
    # meetings and a health band — computed once, not per member
    from collections import defaultdict

    from .incentives import compute_incentives
    from .pnl import _revenue_by_user
    today = timezone.localdate()
    m, y = today.month, today.year
    by_user, _ = _revenue_by_user(m, y)
    attain = {r["user_id"]: (r["revenue"] / r["target"]) if r["target"] else 0.0
              for r in compute_incentives(m, y)["rows"]}
    calls_map, meet_map = defaultdict(int), defaultdict(int)
    for a in (LeadActivity.objects.filter(created_at__year=y, created_at__month=m)
              .values("lead__assigned_to", "activity_type").annotate(c=Count("id"))):
        if a["activity_type"] in CALL_TYPES:
            calls_map[a["lead__assigned_to"]] += a["c"]
        elif a["activity_type"] == "meeting":
            meet_map[a["lead__assigned_to"]] += a["c"]

    members = []
    for u in team:
        kpi = round(min(1.0, attain.get(u.id, 0.0)), 4)
        members.append({
            "id": u.id, "name": u.name, "role": getattr(u.role, "name", ""),
            "employee_id": u.employee_id,
            "leads": Lead.objects.pipeline().filter(assigned_to=u).active().count(),
            "won": Opportunity.objects.filter(assigned_to=u, stage="won").count(),
            "kpi": kpi,
            "revenue": round(float(by_user.get(u.id, 0.0)), 2),
            "calls": calls_map.get(u.id, 0),
            "meetings": meet_map.get(u.id, 0),
            "band": _health_status(kpi),
        })
    return Response({
        "team_size": team.count(),
        "team_leads": leads.active().count(),   # active only
        "team_converted": leads.filter(status="converted").count(),
        "team_open_opportunities": opps.filter(status="open").count(),
        "team_pipeline": _money(opps.filter(status="open"), "expected_revenue"),
        "team_followups": LeadActivity.objects.filter(user_id__in=team_ids).count(),
        "leads_by_status": list(leads.values("status").annotate(count=Count("id")).order_by("status")),
        "members": members,
        "kpis": kpi_scorecard(team_ids),
    })


@api_view(["GET"])
def hr_dashboard(request):
    """HR — people, attendance, leaves, payroll, incentives + learning health."""
    today = timezone.localdate()
    month = today.month
    year = today.year

    # HR & Learning strip (mirrors the Excel monitor). Average KPI = mean target
    # attainment across employees; Critical = attainment below the 60% band.
    # Training / assessment need a Training module the CRM doesn't have yet -> 0.
    inc = compute_incentives(month, year)["rows"]
    attain = [min(1.0, r["revenue"] / r["target"]) for r in inc if r["target"]]
    avg_kpi = round(sum(attain) / len(attain), 4) if attain else 0.0
    active_emps = Employee.objects.filter(user__status="active").count() or Employee.objects.count()
    critical = sum(1 for a in attain if a < 0.6)
    _tstats = _training_stats()

    # Attrition — people who have left / are inactive
    from datetime import timedelta
    total_emp = Employee.objects.count()
    left = Employee.objects.exclude(user__status="active").count()
    attrition_rate = round(left / total_emp, 4) if total_emp else 0.0

    # Document expiry — passports / visas expiring within 60 days (or already expired)
    soon = today + timedelta(days=60)
    from django.db.models import Q
    expiring = (Employee.objects.select_related("user").filter(
        Q(passport_expiry__lte=soon, passport_expiry__isnull=False)
        | Q(visa_expiry__lte=soon, visa_expiry__isnull=False)))
    expiring_docs = []
    for e in expiring:
        for label, d in (("Passport", e.passport_expiry), ("Visa", e.visa_expiry)):
            if d and d <= soon:
                expiring_docs.append({"employee": e.user.name if e.user else "—", "employee_id": e.id,
                                      "doc": label, "expires": d, "days": (d - today).days})
    expiring_docs.sort(key=lambda x: x["days"])

    return Response({
        "total_employees": Employee.objects.count(),
        "present_today": Attendance.objects.filter(date=today, status="present").count(),
        "on_leave_today": Attendance.objects.filter(date=today, status="leave").count(),
        "pending_leaves": Leave.objects.filter(status="pending").count(),
        "attrition_count": left,
        "attrition_rate": attrition_rate,
        "expiring_docs_count": len(expiring_docs),
        "expiring_docs": expiring_docs[:30],
        "payroll_this_month": _money(Payroll.objects.filter(month=month, year=year), "final_salary"),
        "incentives_this_month": _money(Incentive.objects.filter(month=month, year=year), "amount"),
        "leaves_by_status": list(Leave.objects.values("status").annotate(count=Count("id"))),
        "headcount_by_dept": list(
            Employee.objects.values("department__department_name").annotate(count=Count("id")).order_by("-count")
        ),
        "learning": {
            "active_employees": active_emps,
            "average_kpi": avg_kpi,
            "training_compliance": _tstats["compliance"],
            "assessment_pass_rate": _tstats["pass_rate"],
            "overdue_training": _tstats["overdue"],
            "critical_employees": critical,
        },
    })


def _pnl_rows(gross, net, commissions, expenses, payroll, outstanding=0.0):
    """The P&L health table (Excel monitor), computed live. Data-driven: the
    frontend just renders whatever rows come back, so adding a metric here makes
    it appear on the dashboard with no UI change.

    `rate` rows are shown as a percentage; the rest as money. `status` bands:
    a profit/margin is Healthy when >= 0, Critical below; a rate uses 90/70;
    pure cost lines (Direct Cost, Operating Expenses) are informational.

    `outstanding` = the still-uncollected balance on sales (a sale's gross value
    minus what's been collected). It reduces Collected below Gross; when nothing is
    outstanding, Collected == Gross exactly.
    """
    outstanding = max(min(outstanding, gross), 0.0)
    collected = gross - outstanding
    revenue = net
    direct_cost = commissions
    gross_profit = revenue - direct_cost
    operating_expenses = expenses + payroll
    net_operating_profit = gross_profit - operating_expenses
    collection_rate = (collected / gross) if gross else 0.0
    gross_margin = (gross_profit / gross) if gross else 0.0
    net_margin = (net_operating_profit / gross) if gross else 0.0

    def sign(v):
        return "Healthy" if v >= 0 else "Critical"

    def rate_band(v):
        return "Healthy" if v >= 0.9 else ("Watch" if v >= 0.7 else "Critical")

    return [
        {"metric": "Gross Sales", "amount": round(gross, 2), "rate": False, "status": "Healthy"},
        {"metric": "Collected", "amount": round(collected, 2), "rate": False, "status": "Healthy"},
        {"metric": "Outstanding", "amount": round(outstanding, 2), "rate": False,
         "status": "Healthy" if outstanding == 0 else "Watch"},
        {"metric": "Revenue", "amount": round(revenue, 2), "rate": False, "status": sign(revenue)},
        {"metric": "Direct Cost", "amount": round(direct_cost, 2), "rate": False, "status": "Healthy"},
        {"metric": "Gross Profit", "amount": round(gross_profit, 2), "rate": False, "status": sign(gross_profit)},
        {"metric": "Operating Expenses", "amount": round(operating_expenses, 2), "rate": False, "status": "Healthy"},
        {"metric": "Net Operating Profit", "amount": round(net_operating_profit, 2), "rate": False, "status": sign(net_operating_profit)},
        {"metric": "Collection Rate", "amount": round(collection_rate, 4), "rate": True, "status": rate_band(collection_rate)},
        {"metric": "Gross Margin", "amount": round(gross_margin, 4), "rate": True, "status": sign(gross_margin)},
        {"metric": "Net Margin", "amount": round(net_margin, 4), "rate": True, "status": sign(net_margin)},
    ]


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
    # Uncollected balance across sales — a sale's gross value minus what's collected.
    from apps.crm.models import PostSale
    outstanding = sum(max(float(s.gross_value) - float(s.collected_value), 0.0)
                      for s in PostSale.objects.only("gross_value", "collected_value"))
    return Response({
        "gross_revenue": gross,
        "net_revenue": net,
        "total_expenses": expenses,
        "total_commissions": commissions,
        "payroll_this_month": payroll,
        "profit": profit,
        "pnl": _pnl_rows(float(gross), float(net), float(commissions),
                         float(expenses), float(payroll), outstanding),
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
        "kpis": kpi_scorecard(User.objects.values_list("id", flat=True)),
        # active leads only — a converted lead is done (it became a customer)
        "total_leads": Lead.objects.pipeline().active().count(),
        "converted_leads": Lead.objects.pipeline().filter(status="converted").count(),
        "open_opportunities": Opportunity.objects.filter(status="open").count(),
        "pipeline_value": _money(Opportunity.objects.filter(status="open"), "expected_revenue"),
        "won_deals": Opportunity.objects.filter(stage="won").count(),
        "net_revenue": _money(rev, "net_revenue"),
        "by_stage": list(Opportunity.objects.values("stage").annotate(count=Count("id"), value=Sum("expected_revenue")).order_by("stage")),
        "leads_by_source": [
            {"source": d["source__name"] or "Unknown", "count": d["count"]}
            for d in Lead.objects.pipeline().values("source__name").annotate(count=Count("id")).order_by("-count")
        ],
        "top_reps": [
            {"name": u.name, "leads": Lead.objects.pipeline().filter(assigned_to=u).active().count(),
             "won": Opportunity.objects.filter(assigned_to=u, stage="won").count()}
            for u in User.objects.all()[:8]
        ],
    })


@api_view(["GET"])
def leads_by_status(request):
    data = Lead.objects.pipeline().values("status").annotate(count=Count("id")).order_by("status")
    return Response(list(data))


@api_view(["GET"])
def leads_by_source(request):
    data = (Lead.objects.pipeline().values("source__name")
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
    """Monthly net revenue trend. FXArtha supplies its own per-month figures —
    our synced rows all carry the sync date, so grouping them by created_at would
    stack the platform's whole history onto whichever month it was synced. The
    CRM's own revenue is grouped by month and merged in."""
    buckets = {}   # "YYYY-MM" -> {"month": "Mon YYYY", "net": float}
    for m in _fxartha_dashboard().get("revenue_by_month") or []:
        if m.get("brokerage_total"):
            buckets[m.get("month")] = {"month": m.get("label"),
                                       "net": float(m["brokerage_total"])}
    rows = (Revenue.objects.exclude(external_id__startswith="fxa")
            .annotate(m=TruncMonth("created_at")).values("m")
            .annotate(net=Sum("net_revenue")).order_by("m"))
    for d in rows:
        if not d["m"]:
            continue
        b = buckets.setdefault(d["m"].strftime("%Y-%m"),
                               {"month": d["m"].strftime("%b %Y"), "net": 0.0})
        b["net"] += float(d["net"] or 0)
    return Response([buckets[k] for k in sorted(buckets)])


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
def hierarchy(request):
    """The org tree, built from each Employee's manager chain (+ hierarchy level).
    The super admin is never a node — the tree starts at the top real manager.
    Scoped: Super Admin / Finance / HR see the whole company; everyone else (incl.
    a Business Head) sees only their own subtree — themselves + who reports to them."""
    from apps.hr.models import Employee
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    emps = [e for e in Employee.objects.select_related(
        "user", "user__role", "hierarchy_level", "manager").all()
        if e.user and not e.user.is_superuser]
    role = getattr(getattr(request.user, "role", None), "name", "")
    if not (is_admin_view(request.user) or role in ("Finance", "HR")):
        allowed = subordinate_user_ids(request.user, include_self=True)
        emps = [e for e in emps if e.user_id in allowed]
    by_user = {e.user_id: e for e in emps}
    kids = {}
    roots = []
    for e in emps:
        # attach under the manager only if that manager is also a (non-admin) employee
        if e.manager_id and e.manager_id in by_user:
            kids.setdefault(e.manager_id, []).append(e)
        else:
            roots.append(e)

    def node(e):
        children = sorted(kids.get(e.user_id, []), key=lambda x: x.user.name or "")
        child_nodes = [node(c) for c in children]
        return {
            "id": e.user_id,
            "name": e.user.name or "—",
            "email": e.user.email,
            "role": getattr(e.user.role, "name", "") or "",
            "level": e.hierarchy_level.level_name if e.hierarchy_level else "",
            "designation": e.designation or "",
            "reports": len(child_nodes) + sum(c["reports"] for c in child_nodes),
            "children": child_nodes,
        }

    roots.sort(key=lambda e: (e.hierarchy_level.level_order if e.hierarchy_level else 99, e.user.name or ""))
    return Response({"tree": [node(e) for e in roots], "total": len(emps)})


@api_view(["GET"])
@permission_classes([module_required("dagchain")])
def dagchain_overview(request):
    """DAGChain platform snapshot — synced dashboard + node stats + CRM counts."""
    from django.db.models import Sum
    from apps.integrations.models import DagChainNode, DagChainProfile, IntegrationConnection
    conn = IntegrationConnection.objects.filter(platform="dagchain").first()
    cfg = (conn.config or {}) if conn else {}
    nodes = DagChainNode.objects.values("kind").annotate(
        count=Count("id"), revenue=Sum("purchase_price"),
        rewards=Sum("rewards_earned"), blocks=Sum("blocks_validated"))
    prof = DagChainProfile.objects.aggregate(
        users=Count("id"), dgc=Sum("dgc_balance"),
        refs=Sum("referral_count"), earn=Sum("total_referral_earnings"),
        staked=Sum("staked_amount"))
    # Contract-level staking (the "Staking Management" screen): owner, reward pool,
    # DGCC staked and the tranche/stage table, pulled by the sync. The old per-node
    # stakedAmount is kept only as a fallback for a connection synced before this.
    staking = dict(cfg.get("staking") or {})
    staking.setdefault("total_staked", float(prof["staked"] or 0))
    staking.setdefault("stakers", DagChainProfile.objects.filter(staked_amount__gt=0).count())
    # node-level staking (a node's own DGC lock) is separate from the contract
    node_stake = DagChainNode.objects.aggregate(
        staked=Sum("staked_amount"), requirement=Sum("staking_requirement"))
    return Response({
        "dashboard": cfg.get("dashboard", {}),
        "node_stats": cfg.get("node_stats", {}),
        "last_sync": cfg.get("last_sync"),
        "status": conn.status if conn else "disconnected",
        "nodes_by_kind": list(nodes),
        "profiles": prof,
        "node_revenue": float(DagChainNode.objects.aggregate(s=Sum("purchase_price"))["s"] or 0),
        "staking": staking,
        "products": cfg.get("products") or {},
        "node_staking": {
            "staked": float(node_stake["staked"] or 0),
            "requirement": float(node_stake["requirement"] or 0),
            "staked_nodes": DagChainNode.objects.filter(is_staked=True).count(),
        },
    })


@api_view(["GET"])
@permission_classes([module_required("fxartha")])
def fxartha_overview(request):
    """FX Artha platform snapshot — the last-synced dashboard totals + counts."""
    from apps.integrations.models import IntegrationConnection
    from apps.crm.models import Customer
    conn = IntegrationConnection.objects.filter(platform="fxartha").first()
    cfg = (conn.config or {}) if conn else {}
    return Response({
        "dashboard": cfg.get("dashboard", {}),
        "last_sync": cfg.get("last_sync"),
        "status": conn.status if conn else "disconnected",
        "synced_traders": Customer.objects.exclude(external_id="").count(),
    })


@api_view(["GET"])
@permission_classes([module_required("fxartha-traders")])
def fxartha_traders(request):
    """Full FXArtha trader detail: per trader — lots, brokerage, deposits,
    withdrawals, net AUM, contribution, date, RM. Filters: ?q= ?from= ?to=."""
    data = compute_fxartha_traders(
        date_from=request.query_params.get("from"),
        date_to=request.query_params.get("to"),
        q=request.query_params.get("q"),
    )
    return Response(scoped_fxartha_traders(request.user, data))


@api_view(["GET"])
@permission_classes([module_required("fxartha-traders")])
def fxartha_account(request):
    """Live FXArtha account for one synced trader (?customer=<crm id>): account
    metrics, live positions + floating P&L, working orders, ledger, and IB info."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    cust = Customer.objects.filter(id=request.query_params.get("customer")).first()
    if not cust or not cust.external_id:
        return Response({"error": "Not a synced FXArtha trader."}, status=404)
    role = getattr(getattr(request.user, "role", None), "name", "")
    if not (is_admin_view(request.user) or role in ("Finance", "HR")):
        if cust.assigned_to_id not in subordinate_user_ids(request.user, include_self=True):
            return Response({"error": "No access to this trader."}, status=403)
    return Response(fxartha_account_detail(cust))


@api_view(["GET"])
@permission_classes([module_required("dagchain-users")])
def dagchain_account(request):
    """DAGChain account for one synced user (?customer=<crm id>): wallet/DGC
    profile, referrals, KYC, and every validator/storage node with its rewards."""
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    from apps.integrations.models import DagChainProfile, DagChainNode
    cust = Customer.objects.filter(id=request.query_params.get("customer")).first()
    if not cust:
        return Response({"error": "Customer not found."}, status=404)
    prof = DagChainProfile.objects.filter(customer=cust).first()
    if not prof:
        return Response({"error": "Not a synced DAGChain user."}, status=404)
    role = getattr(getattr(request.user, "role", None), "name", "")
    if not (is_admin_view(request.user) or role in ("Finance", "HR")):
        if cust.assigned_to_id not in subordinate_user_ids(request.user, include_self=True):
            return Response({"error": "No access to this user."}, status=403)

    nodes = list(DagChainNode.objects.filter(customer=cust).order_by("kind", "-purchase_price"))

    # commission this user earns for their RM — per node package, at the owner's
    # effective rate (override else universal), so clicking a user shows exactly
    # where their commission comes from
    from apps.hr.models import Employee

    from .commission import load_rules, rate_for
    universal, overrides = load_rules("dagchain")
    owner_emp = (Employee.objects.filter(user_id=cust.assigned_to_id).first()
                 if cust.assigned_to_id else None)
    owner_emp_id = owner_emp.id if owner_emp else None

    def f(v):
        return float(v or 0)

    def node_pct(n):
        return rate_for(universal, overrides, n.package, owner_emp_id) if owner_emp_id else 0.0

    def node_row(n):
        pct = node_pct(n)
        return {
            "id": n.id, "kind": n.kind, "node_key": n.node_key, "package": n.package,
            "purchase_price": f(n.purchase_price), "currency": n.currency,
            "status": n.status, "payment_status": n.payment_status, "uptime": f(n.uptime),
            "blocks_validated": n.blocks_validated, "rewards_earned": f(n.rewards_earned),
            "pending_rewards": f(n.pending_rewards), "claimed_rewards": f(n.claimed_rewards),
            "effective_apy": f(n.effective_apy), "capacity": n.capacity,
            "is_staked": n.is_staked, "staked_amount": f(n.staked_amount),
            "staking_requirement": f(n.staking_requirement), "opened_at": n.opened_at,
            "commission_pct": pct, "commission": round(f(n.purchase_price) * pct / 100, 2),
        }

    profile = {
        "wallet_address": prof.wallet_address, "user_type": prof.user_type,
        "status": prof.status, "kyc_status": prof.kyc_status,
        "email_verified": prof.email_verified, "social_provider": prof.social_provider,
        "dgc_balance": f(prof.dgc_balance), "fuel_wallet_usd": f(prof.fuel_wallet_usd),
        "referral_code": prof.referral_code, "referral_count": prof.referral_count,
        "total_referral_earnings": f(prof.total_referral_earnings),
        "validator_nodes_count": prof.validator_nodes_count,
        "storage_nodes_count": prof.storage_nodes_count,
        "login_count": prof.login_count, "joined_at": prof.joined_at,
        "staked_amount": f(prof.staked_amount), "staked_stakes": prof.staked_stakes,
    }
    totals = {
        "nodes": len(nodes),
        "validator_nodes": sum(1 for n in nodes if n.kind == "validator"),
        "storage_nodes": sum(1 for n in nodes if n.kind == "storage"),
        "node_spend": sum(f(n.purchase_price) for n in nodes),
        "rewards_earned": sum(f(n.rewards_earned) for n in nodes),
        "pending_rewards": sum(f(n.pending_rewards) for n in nodes),
        "claimed_rewards": sum(f(n.claimed_rewards) for n in nodes),
        # real contract stake for this user (per-node stakedAmount is 0)
        "staked": f(prof.staked_amount) or sum(f(n.staked_amount) for n in nodes),
        "staked_stakes": prof.staked_stakes,
        "staked_nodes": sum(1 for n in nodes if n.is_staked),
        # node commission (money) + staking commission (DGC) for this user's RM
        "commission": round(sum(f(n.purchase_price) * node_pct(n) / 100 for n in nodes), 2),
        "comm_staking": round(
            f(prof.staked_amount) * (rate_for(universal, overrides, "staking", owner_emp_id)
                                     if owner_emp_id else 0.0) / 100, 4),
    }
    return Response({
        "customer_id": cust.id,
        "name": prof.display_name or cust.name or (prof.email or "DAGChain User"),
        "email": prof.email or cust.email or "",
        "rm": None if getattr(cust.assigned_to, "is_superuser", False) else getattr(cust.assigned_to, "name", None),
        "profile": profile, "nodes": [node_row(n) for n in nodes], "totals": totals,
    })


@api_view(["GET"])
@permission_classes([module_required("dagchain-users")])
def dagchain_by_rm(request):
    """Per-RM DAGChain book — each employee's assigned users with node counts,
    node spend, per-product commission, rewards, staked, DGC balance and
    referrals. Scoped by role. Rates come from the Commission Rules config."""
    from .dagchain_rm import compute_dagchain_by_rm, scoped_dagchain_by_rm
    emp = request.query_params.get("employee")
    data = compute_dagchain_by_rm(int(emp) if emp else None)
    return Response(scoped_dagchain_by_rm(request.user, data))


@api_view(["GET", "PUT"])
def commission_rules(request):
    """Commission rates per product, with per-RM overrides. Read = the product
    list (with each product's universal rate) plus every override, and the RMs
    a rate can be set for. Write = upsert one rule (admin only).

    PUT body: {platform, product_key, rate, employee?}. employee omitted/null =
    the universal rate; an id = that RM's override. rate blank/"" deletes it.
    """
    from apps.accounts.access import (is_admin_view, subordinate_user_ids,
                                      ASSIGNABLE_LEAD_ROLES)
    from apps.hr.models import Employee
    from apps.integrations.models import CommissionRule

    from .commission import (commission_products, fxartha_catalogue,
                             fxartha_instruments, load_rules)

    can_edit = is_admin_view(request.user)
    if request.method == "PUT":
        if not can_edit:
            return Response({"detail": "Only administrators can change commission rates."}, status=403)
        platform = request.data.get("platform")
        key = request.data.get("product_key")
        if platform not in ("fxartha", "dagchain") or not key:
            return Response({"detail": "platform and product_key are required."}, status=400)
        emp_id = request.data.get("employee") or None
        raw = request.data.get("rate")
        if raw in (None, ""):
            CommissionRule.objects.filter(platform=platform, product_key=key,
                                          employee_id=emp_id).delete()
        else:
            try:
                rate = round(float(raw), 4)
            except (TypeError, ValueError):
                return Response({"rate": "Must be a number."}, status=400)
            defaults = {"rate": rate}
            basis = request.data.get("basis")
            if basis in ("percent", "amount"):
                defaults["basis"] = basis
            CommissionRule.objects.update_or_create(
                platform=platform, product_key=key, employee_id=emp_id,
                defaults=defaults)

    products = commission_products()
    # the RMs an override can target — sales roles who own a book, never the admin
    emps = (Employee.objects.filter(user__role__name__in=ASSIGNABLE_LEAD_ROLES)
            .exclude(user__is_superuser=True).select_related("user"))
    _, fx_over = load_rules("fxartha")
    _, dc_over = load_rules("dagchain")
    return Response({
        "products": products,
        "instruments": {"fxartha": fxartha_instruments()},
        "catalogue": {"fxartha": fxartha_catalogue()},
        "employees": [{"id": e.id, "name": e.user.name} for e in emps],
        "overrides": {"fxartha": {str(k): v for k, v in fx_over.items()},
                      "dagchain": {str(k): v for k, v in dc_over.items()}},
        "can_edit": can_edit,
    })


@api_view(["GET"])
@permission_classes([module_required("fxartha-lots")])
def traders_lots(request):
    """Traders & Lots — per employee: their traders, lots (month + total),
    and estimated per-lot commission. Optional ?rate= overrides the configured
    Activity-Incentive lots rate."""
    today = timezone.localdate()
    month = int(request.query_params.get("month", today.month))
    year = int(request.query_params.get("year", today.year))
    rate = request.query_params.get("rate")
    emp = request.query_params.get("employee")
    data = compute_traders_lots(month, year, float(rate) if rate else None,
                                int(emp) if emp else None)
    return Response(scoped_traders_lots(request.user, data))


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

    # A business fed by an integration (FXArtha / DAGChain) carries its own synced
    # platform snapshot — use it for the headline stats instead of the CRM rows.
    # Match by the connection's business, or by name (the FXArtha connection is
    # global, business=None, but its platform key == "fxartha" == "FX Artha").
    from apps.integrations.models import IntegrationConnection
    _norm = biz.name.replace(" ", "").lower()
    _conn = (IntegrationConnection.objects.filter(business=biz).first()
             or IntegrationConnection.objects.filter(platform=_norm).first())
    platform = _conn.platform if _conn else None
    snap = ((_conn.config or {}).get("dashboard") or {}) if _conn else {}
    # DAGChain's /admin/dashboard reports only approved/active nodes under its
    # "total…" keys, so this snapshot showed 4/1 while the DAGChain Overview (built
    # from every synced node + node revenue) showed 12/4. node-stats carries the
    # true totals — merge it in so both screens agree.
    if platform == "dagchain" and _conn:
        snap = {**snap, **((_conn.config or {}).get("node_stats") or {})}

    rev = Revenue.objects.filter(business=biz)
    month_rev = rev.filter(created_at__year=year, created_at__month=month)

    if platform == "fxartha":
        # FXArtha publishes real per-month figures; the synced rows all carry the
        # sync date, so grouping them by created_at would pile onto one month.
        trend = [{"month": m["label"], "net": float(m["brokerage_total"])}
                 for m in ((_conn.config or {}).get("revenue_by_month") or [])
                 if m.get("brokerage_total")][-6:]
    else:
        trend = list(rev.annotate(m=TruncMonth("created_at")).values("m")
                     .annotate(net=Sum("net_revenue")).order_by("m"))
        trend = [{"month": t["m"].strftime("%b %Y") if t["m"] else "", "net": float(t["net"] or 0)}
                 for t in trend][-6:]

    # KPI cards = this business's OWN metrics (drop cross-business globals).
    # Period: cumulative (default) | month | year | range (?period=&from=&to=).
    period = request.query_params.get("period", "cumulative")
    p_from = request.query_params.get("from")
    p_to = request.query_params.get("to")
    if period == "range" and (p_from or p_to):
        kpi = compute_kpis(None, None, business_id=biz.id, date_from=p_from, date_to=p_to)
    elif period == "month":
        kpi = compute_kpis(month, year, business_id=biz.id)
    elif period == "year":
        kpi = compute_kpis(None, year, business_id=biz.id)
    else:                                        # cumulative — all-time
        kpi = compute_kpis(None, None, business_id=biz.id)
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

    # Customer count: a synced platform's whole user base, not just node/order buyers.
    if platform == "dagchain":
        customer_count = Customer.objects.filter(dagchain__isnull=False).count()
    elif platform == "fxartha":
        customer_count = Customer.objects.exclude(external_id="").filter(dagchain__isnull=True).count()
    else:
        customer_count = Customer.objects.filter(revenues__business=biz).distinct().count()

    # Platform's own dashboard fields, surfaced as labelled cards.
    _STAT_MAP = {
        "dagchain": [("Total Users", "totalUsers", "num"), ("Total Volume", "totalVolume", "money"),
                     ("Validator Nodes", "totalValidatorNodes", "num"), ("Storage Nodes", "totalStorageNodes", "num"),
                     ("Transactions", "totalTransactions", "num"), ("Referrals", "totalReferrals", "num")],
        "fxartha": [("Total Traders", "total_traders", "num"), ("Active Accounts", "active_accounts", "num"),
                    ("Lots Traded", "lots_traded", "num"), ("Total Deposits", "total_deposits", "money"),
                    ("Total Withdrawals", "total_withdrawals", "money")],
    }
    platform_stats = [{"label": lbl, "value": snap.get(key), "kind": kind}
                      for lbl, key, kind in _STAT_MAP.get(platform, []) if snap.get(key) is not None]

    return Response({
        "business": {"id": biz.id, "name": biz.name},
        "month": month, "year": year,
        "platform": platform,
        "platform_stats": platform_stats,
        "gross_revenue": _money(rev, "gross_revenue"),
        "net_revenue": _money(rev, "net_revenue"),
        "month_net_revenue": _money(month_rev, "net_revenue"),
        "customers": customer_count,
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


def _ctc_members(scope, _id, month, year):
    """Resolve the employees covered by a target scope and their CTC."""
    from apps.accounts.models import Team, TeamMember
    from apps.accounts.access import subordinate_user_ids
    User = get_user_model()

    emps = []
    if scope == "user" and _id:
        e = Employee.objects.select_related("user").filter(user_id=_id).first()
        emps = [e] if e else []
    elif scope == "team" and _id:
        team = Team.objects.filter(id=_id).first()
        if team:
            uids = set(TeamMember.objects.filter(team=team).values_list("user_id", flat=True))
            if team.leader_id:
                uids.add(team.leader_id)
            emps = list(Employee.objects.select_related("user").filter(user_id__in=uids))
    elif scope in ("business", "subtree") and _id:
        head = User.objects.filter(id=_id).first()
        if head:
            uids = subordinate_user_ids(head, include_self=True)
            emps = list(Employee.objects.select_related("user").filter(user_id__in=uids))

    rows = [{"user_id": e.user_id, "name": e.user.name if e.user else "—",
             "ctc": round(float(e.monthly_ctc(month, year)), 2)} for e in emps if e]
    return rows


@api_view(["GET"])
def ctc_preview(request):
    """CTC (+ suggested target) for a target scope: individual / team / business.
    Business = the whole management subtree under the chosen head."""
    today = timezone.localdate()
    month = int(request.query_params.get("month") or today.month)
    year = int(request.query_params.get("year") or today.year)
    scope = request.query_params.get("scope", "user")
    try:
        mult = float(request.query_params.get("multiplier") or 1)
    except ValueError:
        mult = 1.0
    rows = _ctc_members(scope, request.query_params.get("id"), month, year)
    total = round(sum(r["ctc"] for r in rows), 2)
    return Response({
        "scope": scope, "month": month, "year": year,
        "ctc": total, "count": len(rows), "members": rows,
        "multiplier": mult, "suggested_target": round(total * mult, 2),
    })


@api_view(["POST"])
def assign_target(request):
    """Create + assign a target (individual/team/business) with the CTC-based value.
    Delegation: Admin can assign to anyone; Business Head / Sales Director only within
    their own subtree; nobody else can assign."""
    from datetime import date
    from apps.accounts.access import can_assign_targets, can_assign_to
    from apps.accounts.models import Team, TeamMember
    from apps.crm.models import Target, TargetAssignment
    from apps.notifications.models import notify

    actor = request.user
    if not can_assign_targets(actor):
        return Response({"detail": "You are not allowed to assign targets."}, status=403)

    d = request.data or {}
    scope = d.get("scope", "user")
    _id = d.get("id")
    if not _id:
        return Response({"detail": "Select who to assign the target to."}, status=400)

    today = timezone.localdate()
    month = int(d.get("month") or today.month)
    year = int(d.get("year") or today.year)
    rows = _ctc_members(scope, _id, month, year)
    if not rows:
        return Response({"detail": "No employees found for this selection."}, status=400)

    # Delegation check against every covered user. A team/business roll-up may
    # include the assigner themselves (they lead it) — an individual target may not.
    allow_self = scope != "user"
    for r in rows:
        if not can_assign_to(actor, r["user_id"], allow_self=allow_self):
            return Response({"detail": "You can only assign within your own team/business."}, status=403)

    try:
        mult = float(d.get("multiplier") or 1)
    except (TypeError, ValueError):
        mult = 1.0
    ctc_total = round(sum(r["ctc"] for r in rows), 2)
    value = d.get("value")
    value = float(value) if value not in (None, "") else round(ctc_total * mult, 2)

    start = d.get("start_date") or date(year, month, 1).isoformat()
    end = d.get("end_date") or date(year, month, 28).isoformat()
    name = d.get("name") or f"{scope.title()} target ({month:02d}/{year})"

    t = Target.objects.create(name=name, target_type=d.get("target_type", "revenue"),
                              value=value, start_date=start, end_date=end)
    if scope == "team":
        TargetAssignment.objects.create(target=t, team_id=_id)
    else:  # user / business -> assign to the chosen user (head)
        TargetAssignment.objects.create(target=t, user_id=_id)

    # notify everyone covered
    from django.contrib.auth import get_user_model
    for u in get_user_model().objects.filter(id__in=[r["user_id"] for r in rows]):
        notify(u, title="New target assigned",
               body=f"{name}: ${value:,.0f} (CTC ${ctc_total:,.0f} × {mult})",
               kind="info", link="/target-board")

    # optional: an incentive/deduction PLAN for these assignees, set with the
    # target. It takes PRIORITY over the global slab schedule and computes from
    # actual attainment when incentives are run:
    #   met  -> base (%/fixed/slab) + over_pct increment on revenue above target
    #   miss -> deduction_pct of target
    incentive = d.get("incentive") or {}
    itype = incentive.get("type")
    inc_result = None
    if itype in ("percentage", "fixed", "slab"):
        from apps.hr.models import Employee, IncentivePlan

        def _f(x):
            try:
                return float(x or 0)
            except (TypeError, ValueError):
                return 0.0

        ival = _f(incentive.get("value"))
        ded_pct = _f(incentive.get("deduction_pct"))
        over_pct = _f(incentive.get("over_pct"))
        plan_slabs = (incentive.get("slabs") or []) if itype == "slab" else []
        made = 0
        for r in rows:
            emp = Employee.objects.filter(user_id=r["user_id"]).first()
            if not emp:
                continue
            IncentivePlan.objects.update_or_create(
                employee=emp, month=month, year=year,
                defaults={"incentive_type": itype, "incentive_value": ival,
                          "slabs": plan_slabs, "deduction_pct": ded_pct, "over_pct": over_pct})
            made += 1
        inc_result = {"type": itype, "employees": made,
                      "deduction_pct": ded_pct, "over_pct": over_pct}

    return Response({"id": t.id, "name": t.name, "value": value, "ctc": ctc_total,
                     "multiplier": mult, "scope": scope, "assignees": len(rows),
                     "incentive": inc_result}, status=201)


@api_view(["GET"])
def kpi_performance(request):
    """Flat, filterable, AUTO-detected KPI performance — one row per employee×metric
    for a month. Derived metrics (calls / meetings / conversions) are computed live
    from CRM activity; manual metrics use their entries. Filter by year / month /
    metric / employee."""
    from apps.crm.models import MetricDefinition
    from .metrics import _leaf_stats
    today = timezone.localdate()
    month = int(request.query_params.get("month") or today.month)
    year = int(request.query_params.get("year") or today.year)
    metric_id = request.query_params.get("metric")
    employee_id = request.query_params.get("employee")

    mdefs = list(MetricDefinition.objects.filter(status="active"))
    if metric_id:
        mdefs = [m for m in mdefs if str(m.id) == str(metric_id)]
    stats = _leaf_stats(mdefs, month, year)

    emps = list(Employee.objects.select_related("user").exclude(user__is_superuser=True))
    # scope to the caller's own subtree (admins / Finance / HR see everyone)
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    role = getattr(getattr(request.user, "role", None), "name", "")
    if not (is_admin_view(request.user) or role in ("Finance", "HR")):
        allowed = subordinate_user_ids(request.user, include_self=True)
        emps = [e for e in emps if e.user_id in allowed]
    if employee_id:
        emps = [e for e in emps if str(e.id) == str(employee_id)]

    rows = []
    for e in emps:
        for m in mdefs:
            val, w = stats.get((e.id, m.id), (0.0, 0))
            if val == 0 and w == 0:
                continue  # only rows with detected activity
            rows.append({
                "employee": e.user.name if e.user else "—", "employee_id": e.id,
                "metric": m.name, "metric_id": m.id, "unit": m.unit,
                "value": round(val, 2), "source": m.source, "category": m.category,
                "month": month, "year": year,
            })
    rows.sort(key=lambda r: (r["metric"], -r["value"]))
    return Response({"month": month, "year": year, "count": len(rows), "rows": rows})


@api_view(["GET"])
@permission_classes([module_required("reports")])
def employee_report(request):
    """One place for upper management: pick an employee, see everything about them
    for a month — attendance, location check-ins, activity, leads, meetings/field
    visits, overdue follow-ups, revenue, KPI metrics and the performance scorecard.

    No ?employee -> returns the pickable employee list (scoped to the caller's tree).
    """
    from datetime import timedelta
    from django.db.models import Max
    from apps.accounts.access import is_admin_view, subordinate_user_ids
    from apps.crm.models import MetricDefinition
    from apps.hr.models import EmployeeActivity
    from .metrics import _leaf_stats
    from .pnl import _revenue_by_user

    today = timezone.localdate()
    month = int(request.query_params.get("month") or today.month)
    year = int(request.query_params.get("year") or today.year)
    role = getattr(getattr(request.user, "role", None), "name", "")
    sees_all = is_admin_view(request.user) or role in ("Finance", "HR")
    allowed = None if sees_all else subordinate_user_ids(request.user, include_self=True)

    # --- picker list (no employee selected yet)
    emp_id = request.query_params.get("employee")
    if not emp_id and not request.query_params.get("all"):
        emps = Employee.objects.select_related("user").exclude(user__is_superuser=True)
        rows = [{"id": e.id, "name": e.user.name,
                 "role": getattr(getattr(e.user, "role", None), "name", "")}
                for e in emps if e.user and (sees_all or e.user_id in allowed)]
        rows.sort(key=lambda r: r["name"])
        return Response({"employees": rows})

    # --- ALL employees, one row each (a table to view / export) — every metric
    # from the single-employee report, one column each.
    if request.query_params.get("all"):
        from collections import defaultdict
        from django.db.models import Count, Q
        from apps.crm.models import MetricDefinition
        mdefs = list(MetricDefinition.objects.filter(status="active"))
        leaf = _leaf_stats(mdefs, month, year)
        by_user, _ = _revenue_by_user(month, year)
        emps = list(Employee.objects.select_related("user", "user__role").exclude(user__is_superuser=True))
        if not sees_all:
            emps = [e for e in emps if e.user_id in allowed]
        emp_ids = [e.id for e in emps]
        user_ids = [e.user_id for e in emps]
        perf = {r["id"]: r for r in compute_performance(month, year)["rows"]}
        leads_qs = Lead.objects.pipeline().filter(assigned_to_id__in=user_ids)
        lc = {r["assigned_to"]: r for r in leads_qs.values("assigned_to").annotate(
            owned=Count("id"), converted=Count("id", filter=Q(status="converted")),
            lost=Count("id", filter=Q(status="lost")),
            open=Count("id", filter=~Q(status__in=["converted", "lost", "nurture"])),
            converted_mo=Count("id", filter=Q(status="converted", converted_at__year=year, converted_at__month=month)))}
        wpipe = defaultdict(float)
        for l in leads_qs.exclude(status__in=["converted", "lost"]).values("assigned_to", "expected_value", "probability"):
            wpipe[l["assigned_to"]] += float(l["expected_value"] or 0) * (l["probability"] or 0) / 100.0
        attmap = {r["employee"]: r for r in Attendance.objects.filter(employee_id__in=emp_ids, date__year=year, date__month=month)
                  .values("employee").annotate(present=Count("id", filter=Q(status__in=["present", "half_day"])),
                                                absent=Count("id", filter=Q(status="absent")), hours=Sum("working_hours"))}
        actmap = {r["employee"]: r for r in EmployeeActivity.objects.filter(employee_id__in=emp_ids, date__year=year, date__month=month)
                  .values("employee").annotate(calls=Sum("calls_completed"), notes=Sum("notes_added"),
                                                tickets=Sum("tickets_updated"), active=Sum("active_duration"), idle=Sum("idle_duration"))}
        meetmap = {r["user"]: r["n"] for r in LeadActivity.objects.filter(user_id__in=user_ids, activity_type="meeting",
                   created_at__year=year, created_at__month=month).values("user").annotate(n=Count("id"))}
        rows = []
        for e in emps:
            p = perf.get(e.id, {})
            l = lc.get(e.user_id, {})
            at = attmap.get(e.id, {})
            ac = actmap.get(e.id, {})
            owned, conv = l.get("owned", 0), l.get("converted", 0)
            row = {
                "employee": e.user.name, "role": getattr(getattr(e.user, "role", None), "name", "") or "",
                "revenue": round(by_user.get(e.user_id, 0.0), 2),
                "overall": p.get("overall", 0), "rank": p.get("rank"), "target_pct": p.get("target_attainment", 0),
                "suggestion": p.get("suggestion", ""),
                "revenue_score": p.get("revenue_score", 0), "growth_score": p.get("growth_score", 0),
                "activity_score": p.get("activity_score", 0),
                "conversion_pct": round(conv / owned * 100, 1) if owned else 0,
                "leads_owned": owned, "leads_open": l.get("open", 0), "leads_converted": conv,
                "leads_lost": l.get("lost", 0), "converted_mo": l.get("converted_mo", 0),
                "weighted_pipeline": round(wpipe.get(e.user_id, 0.0), 2),
                "calls": int(ac.get("calls") or 0), "notes": int(ac.get("notes") or 0),
                "tickets": int(ac.get("tickets") or 0), "meetings": meetmap.get(e.user_id, 0),
                "active_min": int(ac.get("active") or 0), "idle_min": int(ac.get("idle") or 0),
                "present_days": at.get("present", 0), "absent_days": at.get("absent", 0),
                "hours": round(float(at.get("hours") or 0), 1),
            }
            for m in mdefs:
                row[m.name] = round(leaf.get((e.id, m.id), (0.0, 0))[0], 2)
            rows.append(row)
        rows.sort(key=lambda r: r["overall"], reverse=True)
        return Response({"rows": rows, "metric_cols": [m.name for m in mdefs], "month": month, "year": year})

    emp = (Employee.objects.select_related("user", "hierarchy_level", "manager")
           .filter(id=emp_id).exclude(user__is_superuser=True).first())
    if not emp or not emp.user:
        return Response({"found": False})
    if not sees_all and emp.user_id not in allowed:
        return Response({"detail": "Not allowed to view this employee."}, status=403)
    u = emp.user

    # --- attendance + location check-ins (month)
    att = Attendance.objects.filter(employee=emp, date__year=year, date__month=month)
    attendance = {
        "days": att.count(),
        "present": att.filter(status__in=["present", "half_day"]).count(),
        "absent": att.filter(status="absent").count(),
        "leave": att.filter(status="leave").count(),
        "hours": round(float(att.aggregate(t=Sum("working_hours"))["t"] or 0), 1),
    }
    checkins = [{
        "date": a.date, "checkin": a.checkin, "checkout": a.checkout,
        "address": a.checkin_address,
        "map": f"https://www.google.com/maps?q={a.checkin_lat},{a.checkin_lng}" if a.checkin_lat is not None else "",
    } for a in att.order_by("-date")[:31]]

    # --- activity tracking (month)
    agg = (EmployeeActivity.objects.filter(employee=emp, date__year=year, date__month=month)
           .aggregate(calls=Sum("calls_completed"), notes=Sum("notes_added"),
                      tickets=Sum("tickets_updated"), active=Sum("active_duration"), idle=Sum("idle_duration")))
    activity = {k: int(v or 0) for k, v in agg.items()}

    # --- leads owned (current pipeline) + this-month conversions
    leads = Lead.objects.pipeline().filter(assigned_to=u)
    live = leads.exclude(status__in=["converted", "lost"])
    leadstats = {
        "owned": leads.count(),
        "converted": leads.filter(status="converted").count(),
        "converted_month": leads.filter(status="converted", converted_at__year=year, converted_at__month=month).count(),
        "lost": leads.filter(status="lost").count(),
        "open": leads.exclude(status__in=["converted", "lost", "nurture"]).count(),
        "weighted_pipeline": round(sum(float(l.weighted_pipeline or 0) for l in live), 2),
        "conversion_rate": round(leads.filter(status="converted").count() / leads.count() * 100, 1) if leads.count() else 0.0,
    }

    # --- meetings + field-visit locations
    macts = (LeadActivity.objects.filter(user=u, activity_type="meeting")
             .select_related("lead").order_by("-created_at")[:50])
    meetings = [{
        "lead": a.lead.name, "lead_id": a.lead_id, "at": a.meeting_at, "status": a.meeting_status,
        "planned": a.location, "reached": a.visit_address,
        "map": f"https://www.google.com/maps?q={a.visit_lat},{a.visit_lng}" if a.visit_lat is not None else "",
    } for a in macts]
    meetings_month = LeadActivity.objects.filter(
        user=u, activity_type="meeting", created_at__year=year, created_at__month=month).count()

    # --- overdue follow-ups (open leads untouched 3+ days)
    cutoff = timezone.now() - timedelta(days=3)
    open_leads = (leads.exclude(status__in=["converted", "lost", "nurture"])
                  .annotate(last=Max("activities__created_at")))
    overdue = []
    for l in open_leads:
        ref = l.last or l.created_at
        if ref < cutoff:
            overdue.append({"lead": l.name, "lead_id": l.id, "days": (today - ref.date()).days})
    overdue.sort(key=lambda x: -x["days"])

    # --- revenue, KPI metrics, performance scorecard
    by_user, _ = _revenue_by_user(month, year)
    mdefs = list(MetricDefinition.objects.filter(status="active"))
    leaf = _leaf_stats(mdefs, month, year)
    metrics = [{"metric": m.name, "value": round(v, 2), "unit": m.unit, "category": m.category}
               for m in mdefs for v in [leaf.get((emp.id, m.id), (0.0, 0))[0]] if v]
    perf = next((r for r in compute_performance(month, year)["rows"] if r["id"] == emp.id), None)

    return Response({
        "found": True, "month": month, "year": year,
        "profile": {
            "name": u.name, "email": u.email, "role": role if u.id == request.user.id else getattr(getattr(u, "role", None), "name", ""),
            "level": emp.hierarchy_level.level_name if emp.hierarchy_level else None,
            "manager": emp.manager.name if emp.manager else None,
        },
        "attendance": attendance, "checkins": checkins, "activity": activity,
        "leads": leadstats, "meetings": meetings, "meetings_month": meetings_month,
        "overdue_followups": overdue[:30],
        "revenue": round(by_user.get(u.id, 0.0), 2), "metrics": metrics, "performance": perf,
    })


@api_view(["GET"])
def customer_fx(request):
    """Auto-fill values for the AUM / Contribution forms from a customer's synced
    FXArtha data. Select a customer -> deposits, withdrawals, brokerage, insurance,
    staking, trading loss (+ their RM & business) come back."""
    from django.db.models import Sum
    from apps.crm.models import AumEntry, ContributionEntry, Customer
    from apps.hr.models import Employee

    cust = Customer.objects.filter(id=request.query_params.get("customer")).first()
    if not cust:
        return Response({"found": False})
    entry_type = request.query_params.get("entry_type", "deposit")

    # RM (employee) of this customer, via the originating lead
    emp_id = None
    if cust.lead_id and cust.lead.assigned_to_id:
        e = Employee.objects.filter(user_id=cust.lead.assigned_to_id).first()
        emp_id = e.id if e else None

    aum = AumEntry.objects.filter(customer=cust, external_id__startswith="fxa")
    deposit = float(aum.filter(entry_type="deposit").aggregate(s=Sum("amount"))["s"] or 0)
    withdrawal = float(aum.filter(entry_type="withdrawal").aggregate(s=Sum("amount"))["s"] or 0)

    ce = ContributionEntry.objects.filter(customer=cust, external_id__startswith="fxa")
    c = ce.aggregate(b=Sum("brokerage"), i=Sum("insurance"), s=Sum("staking"),
                     t=Sum("trading_loss"), d=Sum("deposit"))

    biz_id = None
    a0, c0 = aum.first(), ce.first()
    if a0:
        biz_id = a0.business_id
    elif c0:
        biz_id = c0.business_id

    # Fallback for manual customers (no FXArtha rows): derive business from the
    # customer's products, revenue, or the originating lead's interest.
    if not biz_id:
        from apps.crm.models import CustomerProduct, LeadInterest
        cp = CustomerProduct.objects.filter(customer=cust).exclude(business__isnull=True).first()
        if cp:
            biz_id = cp.business_id
    if not biz_id:
        rv = Revenue.objects.filter(customer=cust).exclude(business__isnull=True).first()
        if rv:
            biz_id = rv.business_id
    if not biz_id and cust.lead_id:
        from apps.crm.models import LeadInterest
        li = LeadInterest.objects.filter(lead=cust.lead).exclude(business__isnull=True).first()
        if li:
            biz_id = li.business_id

    return Response({
        "found": bool(aum.exists() or ce.exists() or biz_id),
        "employee": emp_id, "business": biz_id,
        "deposit": round(float(c["d"] or deposit), 2), "withdrawal": round(withdrawal, 2),
        "amount": round(withdrawal if entry_type == "withdrawal" else deposit, 2),
        "brokerage": round(float(c["b"] or 0), 2), "insurance": round(float(c["i"] or 0), 2),
        "staking": round(float(c["s"] or 0), 2), "trading_loss": round(float(c["t"] or 0), 2),
    })


def ramped_multiplier(emp, today=None):
    """A salesperson's revenue target ramps with tenure: 6x CTC in month 1,
    8x in month 2, 10x from month 3 onwards."""
    from django.utils import timezone
    today = today or timezone.localdate()
    jd = getattr(emp, "joining_date", None)
    if not jd:
        return 10
    mn = (today.year - jd.year) * 12 + (today.month - jd.month) + 1   # 1-based tenure month
    return 6 if mn <= 1 else 8 if mn == 2 else 10


@api_view(["GET"])
def team_pnl(request):
    """Team-level P&L — Super Admin / Finance / Business Head only. Per team leader:
    their salary, the team's members + CTC, the team's overall CTC, revenue
    generated, profit, and the extra revenue still needed to break into profit."""
    from apps.accounts.access import subordinate_user_ids
    from apps.hr.models import Employee
    from .pnl import _revenue_by_user
    user = request.user
    role = getattr(getattr(user, "role", None), "name", "")
    if not (user.is_superuser or role in ("Super Admin", "Business Head", "Finance")):
        return Response({"detail": "Only Super Admin, Finance or a Business Head can view Team P&L."}, status=403)

    today = timezone.localdate()
    month = int(request.query_params.get("month") or today.month)
    year = int(request.query_params.get("year") or today.year)
    by_user, _ = _revenue_by_user(month, year)
    full = user.is_superuser or role in ("Super Admin", "Finance")
    allowed = None if full else subordinate_user_ids(user, include_self=True)

    tls = (Employee.objects.select_related("user", "user__role")
           .filter(user__role__name="Team Leader").exclude(user__is_superuser=True))
    rows = []
    for tl in tls:
        if not full and tl.user_id not in allowed:
            continue
        ids = list(subordinate_user_ids(tl.user, include_self=True))
        members = list(Employee.objects.select_related("user").filter(user_id__in=ids).exclude(id=tl.id))
        tl_ctc = float(tl.monthly_ctc(month, year))
        members_ctc = sum(float(m.monthly_ctc(month, year)) for m in members)
        team_ctc = round(tl_ctc + members_ctc, 2)
        team_rev = round(sum(float(by_user.get(uid, 0)) for uid in ids), 2)
        profit = round(team_rev - team_ctc, 2)
        rows.append({
            "team_leader": tl.user.name if tl.user else "—", "employee_id": tl.id,
            "tl_salary": round(float(tl.salary or 0), 2), "tl_ctc": round(tl_ctc, 2),
            "member_count": len(members), "members_ctc": round(members_ctc, 2),
            "team_ctc": team_ctc, "revenue": team_rev, "profit": profit,
            "gap_to_profit": round(max(0.0, team_ctc - team_rev), 2),
            "margin": round(profit / team_rev * 100, 1) if team_rev else 0.0,
            "members": [{"name": m.user.name if m.user else "—",
                         "role": getattr(getattr(m.user, "role", None), "name", ""),
                         "ctc": round(float(m.monthly_ctc(month, year)), 2),
                         "revenue": round(float(by_user.get(m.user_id, 0)), 2)} for m in members],
        })
    rows.sort(key=lambda r: r["profit"], reverse=True)
    totals = {k: round(sum(r[k] for r in rows), 2) for k in ("team_ctc", "revenue", "profit", "gap_to_profit")}
    totals["teams"] = len(rows)
    return Response({"month": month, "year": year, "rows": rows, "totals": totals})
