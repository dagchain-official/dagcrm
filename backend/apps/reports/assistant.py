"""Natural-language Q&A over the live CRM database.

A lightweight, deterministic intent router: it reads the question, runs real
Django ORM queries (role-scoped) and returns a grounded, human answer — no
external LLM needed, so it works offline and never hallucinates numbers.
"""
from django.db.models import Count, Sum
from django.utils import timezone

from apps.accounts.access import is_admin_view
from apps.crm.models import Business, Customer, Lead, Opportunity, Product, Proposal
from apps.finance.models import Commission, Expense
from apps.hr.models import Employee, Incentive, Leave, Payroll
from apps.sales.models import Revenue
from apps.support.models import Ticket


def _money(v):
    return f"${(v or 0):,.0f}"


def _role(user):
    return getattr(getattr(user, "role", None), "name", "") or ""


def answer_question(user, question):
    q = (question or "").lower().strip()
    if not q:
        return _help()

    def has(*words):
        return any(w in q for w in words)

    admin = is_admin_view(user)
    role = _role(user)
    can_finance = admin or role == "Finance"
    can_hr = admin or role in ("HR", "Finance")

    # sales entities are scoped to the asker unless they see company-wide data
    leads = Lead.objects.all() if admin else Lead.objects.filter(assigned_to=user)
    opps = Opportunity.objects.all() if admin else Opportunity.objects.filter(assigned_to=user)
    scope_note = "" if admin else " (your assigned records)"

    # ---- company snapshot ---------------------------------------------------
    if has("summary", "overview", "snapshot", "how is", "how's business", "report card", "kaisa chal"):
        return _snapshot(user, admin, can_finance)

    # ---- LEADS --------------------------------------------------------------
    if has("lead"):
        if has("convert", "conversion"):
            total = leads.count()
            won = leads.filter(status="converted").count()
            rate = (won / total * 100) if total else 0
            return f"Conversion rate{scope_note}: {won}/{total} leads converted = {rate:.1f}%."
        if has("unassigned", "not assigned", "without owner"):
            n = Lead.objects.filter(assigned_to__isnull=True).count()
            return f"There are {n} unassigned leads waiting to be distributed."
        if has("source", "channel", "come from", "kaha se"):
            rows = leads.values("source__name").annotate(c=Count("id")).order_by("-c")
            parts = [f"{r['source__name'] or 'Unknown'}: {r['c']}" for r in rows]
            return "Leads by source" + scope_note + " — " + (", ".join(parts) or "none yet") + "."
        if has("status", "stage", "breakdown", "pipeline"):
            rows = leads.values("status").annotate(c=Count("id")).order_by("-c")
            parts = [f"{r['status']}: {r['c']}" for r in rows]
            return "Leads by status" + scope_note + " — " + (", ".join(parts) or "none yet") + "."
        if has("top", "best", "most", "highest") and admin:
            rows = (leads.exclude(assigned_to__isnull=True)
                    .values("assigned_to__name").annotate(c=Count("id")).order_by("-c")[:3])
            parts = [f"{r['assigned_to__name']} ({r['c']})" for r in rows]
            return "Top reps by lead count — " + (", ".join(parts) or "no assignments yet") + "."
        total = leads.count()
        new = leads.filter(status="new").count()
        return f"You have {total} leads{scope_note} — {new} still new/unworked."

    # ---- CUSTOMERS ----------------------------------------------------------
    if has("customer", "client"):
        if has("country", "region", "where"):
            rows = Customer.objects.values("country").annotate(c=Count("id")).order_by("-c")[:6]
            parts = [f"{r['country'] or 'Unknown'}: {r['c']}" for r in rows]
            return "Customers by country — " + (", ".join(parts) or "none yet") + "."
        return f"There are {Customer.objects.count()} customers in the system."

    # ---- OPPORTUNITIES / DEALS ---------------------------------------------
    if has("opportunit", "deal", "pipeline"):
        if has("won", "closed won"):
            n = opps.filter(status="won").count()
            val = opps.filter(status="won").aggregate(t=Sum("expected_revenue"))["t"]
            return f"{n} deals won{scope_note}, worth {_money(val)}."
        if has("lost"):
            return f"{opps.filter(status='lost').count()} deals were lost{scope_note}."
        if has("stage"):
            rows = opps.values("stage").annotate(c=Count("id")).order_by("-c")
            parts = [f"{r['stage']}: {r['c']}" for r in rows]
            return "Opportunities by stage" + scope_note + " — " + (", ".join(parts) or "none") + "."
        openq = opps.exclude(status__in=["won", "lost"])
        val = openq.aggregate(t=Sum("expected_revenue"))["t"]
        return f"{openq.count()} open opportunities{scope_note} worth {_money(val)} in pipeline."

    # ---- PROPOSALS ----------------------------------------------------------
    if has("proposal", "quotation", "quote"):
        cur = Proposal.objects.filter(is_current=True)
        sent = cur.filter(status="sent").count()
        acc = cur.filter(status="accepted").count()
        draft = cur.filter(status="draft").count()
        return (f"Proposals — {cur.count()} total: {draft} draft, {sent} sent, {acc} accepted.")

    # ---- REVENUE / SALES ----------------------------------------------------
    if has("revenue", "sales", "income", "earning", "turnover", "kamai"):
        if not can_finance and not admin:
            return "Revenue figures are visible to admins and Finance only."
        gross = Revenue.objects.aggregate(t=Sum("gross_revenue"))["t"]
        net = Revenue.objects.aggregate(t=Sum("net_revenue"))["t"]
        if has("business", "by business", "which business"):
            rows = (Revenue.objects.values("business__name")
                    .annotate(t=Sum("net_revenue")).order_by("-t")[:6])
            parts = [f"{r['business__name']}: {_money(r['t'])}" for r in rows]
            return "Net revenue by business — " + (", ".join(parts) or "none yet") + "."
        if has("month", "this month"):
            today = timezone.localdate()
            mtd = Revenue.objects.filter(created_at__year=today.year, created_at__month=today.month)
            return f"This month's revenue: {_money(mtd.aggregate(t=Sum('net_revenue'))['t'])} net."
        return f"Gross revenue {_money(gross)}, net revenue {_money(net)} across all businesses."

    # ---- TICKETS / SUPPORT --------------------------------------------------
    if has("ticket", "support", "complaint", "issue"):
        openq = Ticket.objects.exclude(status__in=["resolved", "closed"])
        if has("priority", "urgent", "high"):
            rows = openq.values("priority").annotate(c=Count("id")).order_by("-c")
            parts = [f"{r['priority']}: {r['c']}" for r in rows]
            return "Open tickets by priority — " + (", ".join(parts) or "none open") + "."
        return f"{openq.count()} open tickets out of {Ticket.objects.count()} total."

    # ---- EMPLOYEES / TEAM ---------------------------------------------------
    if has("employee", "staff", "team", "headcount", "people", "kitne log"):
        if not can_hr:
            return "Employee data is visible to admins and HR only."
        if has("department", "dept"):
            rows = Employee.objects.values("department__department_name").annotate(c=Count("id")).order_by("-c")
            parts = [f"{r['department__department_name'] or 'Unassigned'}: {r['c']}" for r in rows]
            return "Employees by department — " + (", ".join(parts) or "none") + "."
        return f"There are {Employee.objects.count()} employees on the team."

    # ---- LEAVES -------------------------------------------------------------
    if has("leave", "time off", "chutti"):
        if not can_hr:
            return "Leave data is visible to admins and HR only."
        p = Leave.objects.filter(status="pending").count()
        a = Leave.objects.filter(status="approved").count()
        return f"Leaves — {p} pending approval, {a} approved."

    # ---- PAYROLL / SALARY ---------------------------------------------------
    if has("payroll", "salary", "payout", "tankhwah"):
        if not can_finance:
            return "Payroll figures are visible to admins and Finance only."
        total = Payroll.objects.aggregate(t=Sum("final_salary"))["t"]
        return f"Total payroll across all payslips: {_money(total)}."

    # ---- INCENTIVES ---------------------------------------------------------
    if has("incentive", "bonus", "reward"):
        if not can_hr:
            return "Incentive data is visible to admins, HR and Finance only."
        total = Incentive.objects.aggregate(t=Sum("amount"))["t"]
        return f"Total incentives paid out: {_money(total)} across {Incentive.objects.count()} entries."

    # ---- EXPENSES -----------------------------------------------------------
    if has("expense", "cost", "spend", "kharch"):
        if not can_finance:
            return "Expense figures are visible to admins and Finance only."
        if has("type", "category"):
            rows = Expense.objects.values("expense_type").annotate(t=Sum("amount")).order_by("-t")
            parts = [f"{r['expense_type']}: {_money(r['t'])}" for r in rows]
            return "Expenses by type — " + (", ".join(parts) or "none") + "."
        return f"Total expenses recorded: {_money(Expense.objects.aggregate(t=Sum('amount'))['t'])}."

    # ---- COMMISSIONS --------------------------------------------------------
    if has("commission", "partner payout"):
        if not can_finance:
            return "Commission figures are visible to admins and Finance only."
        total = Commission.objects.aggregate(t=Sum("amount"))["t"]
        return f"Total partner commissions: {_money(total)}."

    # ---- BUSINESSES / PRODUCTS ---------------------------------------------
    if has("business", "vertical", "company"):
        names = list(Business.objects.values_list("name", flat=True))
        return f"{len(names)} businesses: {', '.join(names) or 'none'}."
    if has("product", "service", "plan"):
        return f"There are {Product.objects.count()} products/services across all businesses."

    return _help()


def _snapshot(user, admin, can_finance):
    leads = Lead.objects.all() if admin else Lead.objects.filter(assigned_to=user)
    lines = [
        f"📊 Leads: {leads.count()} ({leads.filter(status='converted').count()} converted)",
        f"👥 Customers: {Customer.objects.count()}",
        f"🎯 Open deals: {Opportunity.objects.exclude(status__in=['won','lost']).count()}",
    ]
    if can_finance or admin:
        net = Revenue.objects.aggregate(t=Sum('net_revenue'))['t']
        lines.append(f"💰 Net revenue: {_money(net)}")
    lines.append(f"🎫 Open tickets: {Ticket.objects.exclude(status__in=['resolved','closed']).count()}")
    return "Company snapshot —\n" + "\n".join(lines)


def _help():
    return (
        "Ask me anything about your data, for example:\n"
        "• How many leads do we have? · Lead conversion rate · Leads by source\n"
        "• Open opportunities / pipeline value · Deals won\n"
        "• Total revenue · Revenue by business · This month's sales\n"
        "• Proposals sent vs accepted · Open tickets by priority\n"
        "• How many employees? · Pending leaves · Total expenses\n"
        "Type 'summary' for a full company snapshot."
    )
