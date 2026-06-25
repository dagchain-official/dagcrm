"""Natural-language Q&A over the live CRM database.

A lightweight, deterministic intent router: it reads the question, runs real
Django ORM queries (role-scoped) and returns a grounded, human answer — no
external LLM needed, so it works offline and never hallucinates numbers.
"""
import re

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.accounts.access import is_admin_view
from apps.crm.models import (
    Business, Customer, Lead, LeadActivity, Opportunity, Product, Proposal,
)
from apps.finance.models import Commission, Expense
from apps.hr.models import Attendance, Employee, EmployeeActivity, Incentive, Leave, Payroll
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

    # ---- specific record lookup (type a name -> full profile) ---------------
    record = _lookup_record(user, question, q, admin, role, can_hr)
    if record:
        return record

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
        "Or just type a name to see a full profile — e.g. \"Aarav Iyer\", "
        "\"find LD0007\", \"employee Riya\".\n"
        "Type 'summary' for a full company snapshot."
    )


# ----------------------------------------------------------------------------
# Specific-record lookup: type any lead / customer / employee name (or code)
# and get a full role-scoped profile back.
# ----------------------------------------------------------------------------
_AGG_WORDS = (
    "lead", "customer", "client", "opportunit", "deal", "pipeline", "proposal",
    "quot", "revenue", "sales", "income", "earning", "turnover", "ticket",
    "support", "complaint", "issue", "employee", "staff", "team", "headcount",
    "people", "leave", "payroll", "salary", "incentive", "bonus", "expense",
    "commission", "business", "product", "service", "summary", "overview",
    "snapshot", "how many", "total", "conversion", "by source", "kitne",
)
_PREFIX_VERBS = (
    "who is", "find", "details of", "detail of", "profile of", "info about",
    "information about", "show me", "show", "lookup", "look up", "search",
    "tell me about", "get me", "open",
)
_SUFFIX_PHRASES = (
    "ki detail", "ka detail", "ki details", "ka data", "ki jankari",
    "ki info", "ke baare", "ka profile", "ki profile",
)
_TYPE_WORDS = {"employee": "employee", "staff": "employee", "lead": "lead",
               "customer": "customer", "client": "customer"}


def _extract_name(raw, q):
    """Pull the searched name + optional entity-type hint out of a question."""
    typ = None

    # leading "employee/lead/customer <name>"
    m = re.match(r"^(employee|staff|lead|customer|client)\s+(.+)$", q)
    if m:
        return _TYPE_WORDS[m.group(1)], m.group(2).strip(" ?.")

    # "<name> ki detail" (Hinglish suffix)
    for s in _SUFFIX_PHRASES:
        if s in q:
            return None, q.split(s)[0].strip(" ?.")

    # "find/who is/details of <name>" (English prefix verb)
    for v in _PREFIX_VERBS:
        if q.startswith(v + " ") or q == v:
            name = q[len(v):].strip(" ?.")
            name = re.sub(r"^(the|a|lead|customer|employee|staff|client)\s+", "", name)
            return typ, name

    # bare name typed directly — only if it has no aggregate keyword
    if not any(w in q for w in _AGG_WORDS) and 1 <= len(q.split()) <= 4:
        return None, q.strip(" ?.")

    return None, None


def _lookup_record(user, raw, q, admin, role, can_hr):
    typ, name = _extract_name(raw, q)
    if not name or len(name) < 2:
        return None

    can_customers = admin or role in ("Sales Manager", "Team Leader", "Sales Executive", "Support")
    leads_qs = Lead.objects.all() if admin else Lead.objects.filter(assigned_to=user)

    matches = []  # (kind, obj, label)
    if typ in (None, "lead"):
        for l in leads_qs.filter(
            Q(name__icontains=name) | Q(lead_code__iexact=name) |
            Q(email__icontains=name) | Q(phone__icontains=name)
        ).select_related("source", "assigned_to")[:6]:
            matches.append(("lead", l, f"Lead · {l.lead_code} {l.name}"))
    if typ in (None, "customer") and can_customers:
        for c in Customer.objects.filter(
            Q(name__icontains=name) | Q(email__icontains=name) | Q(phone__icontains=name)
        )[:6]:
            matches.append(("customer", c, f"Customer · {c.name}"))
    if typ in (None, "employee") and can_hr:
        for e in Employee.objects.filter(
            Q(user__name__icontains=name) | Q(user__email__icontains=name) |
            Q(user__employee_id__iexact=name)
        ).select_related("user", "department", "manager")[:6]:
            matches.append(("employee", e, f"Employee · {e.user.name}"))

    if not matches:
        # a name was clearly asked for but nothing matched (or no permission)
        looked_like_request = typ or any(
            q.startswith(v + " ") for v in _PREFIX_VERBS) or any(s in q for s in _SUFFIX_PHRASES)
        if looked_like_request:
            return (f"No record found for \"{name}\". Try the exact name, lead code "
                    "(e.g. LD0007), email or phone — or check you have access to it.")
        return None

    if len(matches) > 1:
        lines = [f"Found {len(matches)} matches for \"{name}\":"]
        lines += [f"• {lbl}" for _, _, lbl in matches]
        lines.append("Type the exact name (ya code) to open the full profile.")
        return "\n".join(lines)

    kind, obj, _ = matches[0]
    if kind == "lead":
        return _lead_profile(obj)
    if kind == "customer":
        return _customer_profile(obj)
    return _employee_profile(obj, show_salary=can_hr)


def _lead_profile(l):
    acts = l.activities.select_related("user").all()
    last = acts.first()
    opps = l.opportunities.count()
    props = l.proposals.filter(is_current=True).count()
    interests = ", ".join(
        i.business.name for i in l.interests.select_related("business").all() if i.business
    ) or "—"
    lines = [
        f"👤 LEAD — {l.name}  ({l.lead_code})",
        f"Status: {l.status} · Score: {l.score}/100",
        f"📞 {l.phone or '—'}   ✉️ {l.email or '—'}",
        f"🌍 {l.country or '—'} · Source: {l.source.name if l.source else '—'}",
        f"Owner: {l.assigned_to.name if l.assigned_to else 'Unassigned'}",
        f"Interested in: {interests}",
        f"Activities: {acts.count()} · Opportunities: {opps} · Proposals: {props}",
    ]
    if last:
        lines.append(f"Last activity: {last.activity_type} — "
                     f"{(last.remarks or last.next_action or '')[:60]}")
    return "\n".join(lines)


def _customer_profile(c):
    revs = Revenue.objects.filter(customer=c).select_related("business")
    net = revs.aggregate(t=Sum("net_revenue"))["t"] or 0
    gross = revs.aggregate(t=Sum("gross_revenue"))["t"] or 0
    prods = c.products.select_related("business", "product").all()
    tickets = Ticket.objects.filter(customer=c)
    open_t = tickets.exclude(status__in=["resolved", "closed"]).count()
    prod_list = ", ".join(
        f"{p.product.name if p.product else (p.business.name if p.business else '')}"
        for p in prods
    ) or "—"
    lines = [
        f"🧑‍💼 CUSTOMER — {c.name}",
        f"📞 {c.phone or '—'}   ✉️ {c.email or '—'}   🌍 {c.country or '—'}",
        f"💰 Net revenue: {_money(net)}  (gross {_money(gross)})",
        f"📦 Products ({prods.count()}): {prod_list}",
        f"🎫 Tickets: {open_t} open / {tickets.count()} total",
    ]
    if c.lead_id:
        lines.append(f"Originated from lead: {c.lead.lead_code}")
    return "\n".join(lines)


def _employee_profile(e, show_salary=True):
    u = e.user
    att = e.attendance.all()[:5]
    present = sum(1 for a in att if a.status == "present")
    leaves = e.leaves.all()
    pend = leaves.filter(status="pending").count()
    pay = e.payrolls.order_by("-year", "-month").first()
    act = e.activities.all()[:30]
    calls = sum(a.calls_completed for a in act)
    notes = sum(a.notes_added for a in act)
    lines = [
        f"👔 EMPLOYEE — {u.name}  ({u.employee_id or '—'})",
        f"Role: {getattr(u.role, 'name', '—')} · {e.designation or '—'}",
        f"Department: {e.department.department_name if e.department else '—'}",
        f"Manager: {e.manager.name if e.manager else '—'}",
        f"Joined: {e.joining_date or '—'}",
        f"✉️ {u.email}",
    ]
    if show_salary:
        lines.append(f"💵 Salary: {_money(e.salary)}")
        if pay:
            lines.append(f"🧾 Latest payroll ({pay.month}/{pay.year}): "
                         f"net {_money(pay.final_salary)}")
    lines.append(f"🕒 Attendance (last {len(att)}): {present} present")
    lines.append(f"🌴 Leaves: {pend} pending / {leaves.count()} total")
    lines.append(f"📈 Recent activity: {calls} calls, {notes} notes")
    return "\n".join(lines)
