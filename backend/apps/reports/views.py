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


def _money(qs, field):
    return qs.aggregate(t=Sum(field))["t"] or 0


def _scoped_revenue(user):
    qs = Revenue.objects.all()
    ids = allowed_business_ids(user)
    return qs.filter(business_id__in=ids) if ids is not None else qs


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
    """Personal KPIs scoped to the logged-in user."""
    user = request.user
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
    # FXArtha reports its own platform revenue — take it as-is and drop only its
    # per-trader rows so they aren't double-counted. Every other source still
    # counts: the CRM's own revenue and other integrations (e.g. DAGChain nodes).
    fx_revenue = float(_fxartha_dashboard().get("total_revenue") or 0)
    other_revenue = Revenue.objects.exclude(external_id__startswith="fxa")
    gross = float(_money(other_revenue, "gross_revenue")) + fx_revenue
    net = float(_money(other_revenue, "net_revenue")) + fx_revenue
    reps = []
    for u in User.objects.all():
        leads = Lead.objects.pipeline().filter(assigned_to=u).count()
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
        "total_leads": Lead.objects.pipeline().count(),
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


@api_view(["GET"])
def team_dashboard(request):
    """Team Leader — data for the leader's direct reports."""
    team = User.objects.filter(manager=request.user)
    team_ids = list(team.values_list("id", flat=True)) + [request.user.id]
    leads = Lead.objects.pipeline().filter(assigned_to_id__in=team_ids)
    opps = Opportunity.objects.filter(assigned_to_id__in=team_ids)
    members = [
        {
            "id": u.id, "name": u.name, "role": getattr(u.role, "name", ""),
            "leads": Lead.objects.pipeline().filter(assigned_to=u).count(),
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
        "total_leads": Lead.objects.pipeline().count(),
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
            {"name": u.name, "leads": Lead.objects.pipeline().filter(assigned_to=u).count(),
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
    The super admin is never a node — the tree starts at the top real manager."""
    from apps.hr.models import Employee
    emps = [e for e in Employee.objects.select_related(
        "user", "user__role", "hierarchy_level", "manager").all()
        if e.user and not e.user.is_superuser]
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
        refs=Sum("referral_count"), earn=Sum("total_referral_earnings"))
    return Response({
        "dashboard": cfg.get("dashboard", {}),
        "node_stats": cfg.get("node_stats", {}),
        "last_sync": cfg.get("last_sync"),
        "status": conn.status if conn else "disconnected",
        "nodes_by_kind": list(nodes),
        "profiles": prof,
        "node_revenue": float(DagChainNode.objects.aggregate(s=Sum("purchase_price"))["s"] or 0),
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
@permission_classes([module_required("fxartha")])
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
@permission_classes([module_required("fxartha")])
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
@permission_classes([module_required("dagchain")])
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

    def f(v):
        return float(v or 0)

    def node_row(n):
        return {
            "id": n.id, "kind": n.kind, "node_key": n.node_key, "package": n.package,
            "purchase_price": f(n.purchase_price), "currency": n.currency,
            "status": n.status, "payment_status": n.payment_status, "uptime": f(n.uptime),
            "blocks_validated": n.blocks_validated, "rewards_earned": f(n.rewards_earned),
            "pending_rewards": f(n.pending_rewards), "claimed_rewards": f(n.claimed_rewards),
            "effective_apy": f(n.effective_apy), "capacity": n.capacity,
            "is_staked": n.is_staked, "staked_amount": f(n.staked_amount),
            "staking_requirement": f(n.staking_requirement), "opened_at": n.opened_at,
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
    }
    totals = {
        "nodes": len(nodes),
        "validator_nodes": sum(1 for n in nodes if n.kind == "validator"),
        "storage_nodes": sum(1 for n in nodes if n.kind == "storage"),
        "node_spend": sum(f(n.purchase_price) for n in nodes),
        "rewards_earned": sum(f(n.rewards_earned) for n in nodes),
        "pending_rewards": sum(f(n.pending_rewards) for n in nodes),
        "claimed_rewards": sum(f(n.claimed_rewards) for n in nodes),
        "staked": sum(f(n.staked_amount) for n in nodes),
        "staked_nodes": sum(1 for n in nodes if n.is_staked),
    }
    return Response({
        "customer_id": cust.id,
        "name": prof.display_name or cust.name or (prof.email or "DAGChain User"),
        "email": prof.email or cust.email or "",
        "rm": getattr(cust.assigned_to, "name", None),
        "profile": profile, "nodes": [node_row(n) for n in nodes], "totals": totals,
    })


@api_view(["GET"])
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

    # Delegation check against every covered user.
    for r in rows:
        if not can_assign_to(actor, r["user_id"]):
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

    return Response({"id": t.id, "name": t.name, "value": value, "ctc": ctc_total,
                     "multiplier": mult, "scope": scope, "assignees": len(rows)}, status=201)


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
