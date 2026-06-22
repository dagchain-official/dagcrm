import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Role, Team, TeamMember
from apps.crm.models import (
    Business, Communication, Customer, CustomerProduct, Lead, LeadActivity,
    LeadInterest, LeadSource, Opportunity, Product, Target,
)
from apps.finance.models import Commission, Expense
from apps.hr.models import (
    Attendance, Department, Employee, EmployeeActivity, Incentive, IncentiveRule,
    Leave, LeaveType, Payroll,
)
from apps.sales.models import Revenue
from apps.support.models import Ticket, TicketComment

User = get_user_model()

ROLES = ["Super Admin", "Business Head", "Regional Manager", "Team Leader",
         "RM", "Support", "HR", "Finance"]
BUSINESSES = ["FX Artha", "DAGChain", "DAGGPT", "DAGDB", "Energy DAO", "DAG Army"]
SOURCES = ["Meta Ads", "Google Ads", "WhatsApp", "Telegram", "Website",
           "Referral", "Manual", "CSV"]
COUNTRIES = ["India", "UAE", "USA", "UK", "Singapore", "Germany"]
FIRST = ["Aarav", "Vivaan", "Diya", "Saanvi", "Reyansh", "Anaya", "Kabir",
         "Myra", "Arjun", "Ishaan", "Zara", "Ayaan", "Riya", "Vihaan", "Kiara"]


class Command(BaseCommand):
    help = "Seed demo data for DAGOS CRM"

    def handle(self, *args, **opts):
        if Business.objects.exists():
            self.stdout.write(self.style.WARNING("Data already seeded. Skipping."))
            return

        rnd = random.Random(42)
        self.stdout.write("Seeding roles & users...")
        roles = {r: Role.objects.create(name=r) for r in ROLES}

        admin = User.objects.create_superuser(
            email="admin@dagos.com", password="admin123",
            name="Super Admin", employee_id="EMP001", role=roles["Super Admin"],
        )
        users = [admin]
        designations = ["Sales Executive", "Relationship Manager", "Team Lead",
                        "Support Agent", "HR Executive", "Finance Analyst"]
        for i in range(2, 16):
            role = rnd.choice(list(roles.values()))
            u = User.objects.create_user(
                email=f"user{i}@dagos.com", password="user123",
                name=f"{rnd.choice(FIRST)} {rnd.choice(['Sharma','Patel','Khan','Rao','Singh','Mehta'])}",
                employee_id=f"EMP{i:03d}", role=role, manager=admin,
            )
            users.append(u)

        # Businesses + products
        self.stdout.write("Seeding businesses & products...")
        businesses, products = [], []
        for bname in BUSINESSES:
            b = Business.objects.create(name=bname, description=f"{bname} product line")
            businesses.append(b)
            for n in range(1, rnd.randint(2, 4)):
                products.append(Product.objects.create(business=b, name=f"{bname} Plan {n}"))

        sources = [LeadSource.objects.create(name=s) for s in SOURCES]

        # Leads + interests + activities
        self.stdout.write("Seeding leads, activities, opportunities...")
        lead_statuses = ["new", "contacted", "qualified", "converted", "lost"]
        leads = []
        for i in range(1, 121):
            lead = Lead.objects.create(
                lead_code=f"LD{i:04d}",
                name=f"{rnd.choice(FIRST)} {rnd.choice(['Gupta','Verma','Nair','Bose','Iyer'])}",
                email=f"lead{i}@example.com",
                phone=f"+91{rnd.randint(7000000000, 9999999999)}",
                country=rnd.choice(COUNTRIES),
                source=rnd.choice(sources),
                assigned_to=rnd.choice(users),
                created_by=admin,
                status=rnd.choice(lead_statuses),
                score=rnd.randint(10, 95),
            )
            leads.append(lead)
            b = rnd.choice(businesses)
            LeadInterest.objects.create(lead=lead, business=b,
                                        product=rnd.choice([p for p in products if p.business_id == b.id] or [None]))
            for _ in range(rnd.randint(0, 3)):
                LeadActivity.objects.create(
                    lead=lead, user=lead.assigned_to,
                    activity_type=rnd.choice(["call", "whatsapp", "email", "meeting", "note"]),
                    remarks=rnd.choice(["Interested", "Asked for pricing", "Follow up next week",
                                        "Not reachable", "Requested demo"]),
                    followup_date=date.today() + timedelta(days=rnd.randint(1, 14)),
                )

        # Opportunities
        for lead in rnd.sample(leads, 60):
            Opportunity.objects.create(
                lead=lead, product=rnd.choice(products), assigned_to=lead.assigned_to,
                stage=rnd.choice(["proposal", "negotiation", "won", "lost", "active"]),
                expected_revenue=Decimal(rnd.randint(500, 50000)),
                status=rnd.choice(["open", "closed"]),
            )

        # Customers (from converted leads) + products + revenue
        self.stdout.write("Seeding customers, revenue, communications...")
        customers = []
        for lead in [l for l in leads if l.status == "converted"] or leads[:25]:
            c = Customer.objects.create(name=lead.name, email=lead.email,
                                        phone=lead.phone, country=lead.country, lead=lead)
            customers.append(c)
            b = rnd.choice(businesses)
            prod = rnd.choice([p for p in products if p.business_id == b.id] or products)
            CustomerProduct.objects.create(customer=c, business=b, product=prod, status="active")
            gross = Decimal(rnd.randint(1000, 60000))
            comm = (gross * Decimal(rnd.randint(5, 20)) / Decimal(100)).quantize(Decimal("0.01"))
            Revenue.objects.create(customer=c, business=b, product=prod,
                                   gross_revenue=gross, commission=comm)
            Communication.objects.create(customer=c, channel=rnd.choice(["whatsapp", "email", "sms", "telegram"]),
                                         message="Welcome to DAGOS!", direction="outbound")

        # Targets
        for b in businesses:
            Target.objects.create(name=f"{b.name} Q-Target", target_type="revenue",
                                  value=Decimal(rnd.randint(100000, 500000)), business=b,
                                  start_date=date.today().replace(day=1),
                                  end_date=date.today() + timedelta(days=90))

        # Teams
        for i in range(3):
            t = Team.objects.create(name=f"Team {chr(65+i)}", leader=rnd.choice(users))
            for u in rnd.sample(users, 4):
                TeamMember.objects.get_or_create(team=t, user=u)

        # Support tickets
        self.stdout.write("Seeding support tickets...")
        for i in range(1, 41):
            t = Ticket.objects.create(
                ticket_no=f"TK{i:04d}", customer=rnd.choice(customers) if customers else None,
                category=rnd.choice(["Billing", "Technical", "Account", "General"]),
                priority=rnd.choice(["low", "medium", "high", "urgent"]),
                status=rnd.choice(["open", "assigned", "in_progress", "resolved", "closed"]),
                assigned_to=rnd.choice(users),
            )
            TicketComment.objects.create(ticket=t, user=rnd.choice(users),
                                         comment="Looking into this issue.")

        # HR
        self.stdout.write("Seeding HR, payroll, incentives...")
        departments = [Department.objects.create(department_name=d)
                       for d in ["Sales", "Support", "HR", "Finance", "Tech"]]
        leave_types = [LeaveType.objects.create(leave_name=n)
                       for n in ["Casual", "Sick", "Earned", "Unpaid"]]
        employees = []
        for u in users:
            emp = Employee.objects.create(
                user=u, department=rnd.choice(departments),
                designation=rnd.choice(designations),
                salary=Decimal(rnd.randint(20000, 90000)),
                joining_date=date.today() - timedelta(days=rnd.randint(30, 1000)),
                manager=admin if u != admin else None,
            )
            employees.append(emp)
            for d in range(5):
                day = date.today() - timedelta(days=d)
                Attendance.objects.create(
                    employee=emp, date=day,
                    checkin=timezone.now() - timedelta(hours=9),
                    checkout=timezone.now(),
                    working_hours=Decimal(rnd.randint(6, 9)),
                    status=rnd.choice(["present", "present", "present", "half_day", "leave"]),
                )
                EmployeeActivity.objects.create(
                    employee=emp, date=day,
                    login_duration=rnd.randint(300, 540), active_duration=rnd.randint(200, 480),
                    idle_duration=rnd.randint(10, 120), calls_completed=rnd.randint(0, 30),
                    notes_added=rnd.randint(0, 20), tickets_updated=rnd.randint(0, 10),
                )
            Leave.objects.create(employee=emp, leave_type=rnd.choice(leave_types),
                                 start_date=date.today() + timedelta(days=5),
                                 end_date=date.today() + timedelta(days=7),
                                 reason="Personal", status=rnd.choice(["pending", "approved", "rejected"]))
            Payroll.objects.create(employee=emp, basic_salary=emp.salary,
                                   incentive=Decimal(rnd.randint(0, 10000)),
                                   bonus=Decimal(rnd.randint(0, 5000)),
                                   deduction=Decimal(rnd.randint(0, 3000)),
                                   month=date.today().month, year=date.today().year)

        rules = []
        for b in businesses:
            rules.append(IncentiveRule.objects.create(business=b, formula_type="percentage",
                                                       formula_value=Decimal(rnd.randint(2, 10))))
        for emp in employees:
            Incentive.objects.create(employee=emp, rule=rnd.choice(rules),
                                     amount=Decimal(rnd.randint(1000, 15000)),
                                     month=date.today().month, year=date.today().year)

        # Finance
        self.stdout.write("Seeding finance...")
        for _ in range(30):
            Expense.objects.create(department=rnd.choice(departments),
                                   amount=Decimal(rnd.randint(1000, 40000)),
                                   expense_type=rnd.choice(["Salary", "Marketing", "Rent", "Tools", "Travel"]),
                                   description="Monthly expense",
                                   date=date.today() - timedelta(days=rnd.randint(0, 90)))
        for _ in range(15):
            Commission.objects.create(partner_name=f"Partner {rnd.randint(1, 20)}",
                                      amount=Decimal(rnd.randint(2000, 50000)),
                                      business=rnd.choice(businesses),
                                      date=date.today() - timedelta(days=rnd.randint(0, 90)))

        self.stdout.write(self.style.SUCCESS(
            "Seed complete. Login: admin@dagos.com / admin123"))
