from django.conf import settings
from django.db import models


# ------------------------------------------------------------------ Business
class Business(models.Model):
    """FX Artha, DAGChain, DAGGPT, DAGDB, Energy DAO, DAG Army."""

    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    # How a product earns — drives the Revenue Engine (nothing hardcoded).
    REVENUE_TYPE = [
        ("one_time", "One-Time Sale"),       # Developer Node, course, property unit
        ("recurring", "Recurring / Subscription"),  # DAGGPT subscription, API
        ("per_unit", "Per Unit"),            # Storage Node ($/GB), lots
        ("token", "Token Purchase"),         # DGCC coin — dollar value sold
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    # free-form category so admins can add any product family without code changes
    product_type = models.CharField(max_length=60, blank=True)  # Node, Coin, Subscription, Course…
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revenue_type = models.CharField(max_length=20, choices=REVENUE_TYPE, default="one_time")
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    def __str__(self):
        return f"{self.name} ({self.business.name})"


# ------------------------------------------------------------------ Leads
class LeadSource(models.Model):
    """Meta Ads, Google Ads, WhatsApp, Telegram, Website, Referral, Manual, CSV."""

    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    STATUS = [
        ("new", "New"), ("contacted", "Contacted"), ("qualified", "Qualified"),
        ("converted", "Converted"), ("lost", "Lost"),
    ]
    lead_code = models.CharField(max_length=40, unique=True)
    external_id = models.CharField(max_length=64, blank=True, db_index=True)  # id in an external system (e.g. FXArtha)
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_leads")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_leads")
    status = models.CharField(max_length=20, choices=STATUS, default="new")
    score = models.PositiveIntegerField(default=0)  # AI lead score (0-100)
    converted_at = models.DateTimeField(null=True, blank=True)  # set when status -> converted
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # stamp the moment of conversion so KPIs credit the right month
        if self.status == "converted" and not self.converted_at:
            from django.utils import timezone
            self.converted_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lead_code} - {self.name}"


class LeadInterest(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="interests")
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ("lead", "business", "product")


class LeadActivity(models.Model):
    TYPES = [("call", "Call"), ("whatsapp", "WhatsApp"), ("email", "Email"),
             ("meeting", "Meeting"), ("note", "Note"), ("proposal", "Proposal")]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=TYPES, default="call")
    remarks = models.TextField(blank=True)
    followup_date = models.DateField(null=True, blank=True)
    next_action = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Lead activities"
        ordering = ["-created_at"]


# ------------------------------------------------------------------ Opportunities
class Opportunity(models.Model):
    STAGE = [("proposal", "Proposal"), ("negotiation", "Negotiation"),
             ("won", "Won"), ("lost", "Lost"), ("active", "Active")]
    STATUS = [("open", "Open"), ("closed", "Closed")]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="opportunities")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="opportunities")
    stage = models.CharField(max_length=20, choices=STAGE, default="active")
    expected_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ["-created_at"]


# ------------------------------------------------------------------ Customers
class Customer(models.Model):
    name = models.CharField(max_length=150)
    external_id = models.CharField(max_length=64, blank=True, db_index=True)  # external system id (e.g. FXArtha user)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="customers")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CustomerProduct(models.Model):
    STATUS = [("active", "Active"), ("expired", "Expired"), ("cancelled", "Cancelled")]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="products")
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="active")


# ------------------------------------------------------------------ Communications
class Communication(models.Model):
    CHANNELS = [("whatsapp", "WhatsApp"), ("email", "Email"), ("sms", "SMS"), ("telegram", "Telegram")]
    DIRECTION = [("inbound", "Inbound"), ("outbound", "Outbound")]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name="communications")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name="communications")
    channel = models.CharField(max_length=20, choices=CHANNELS, default="whatsapp")
    message = models.TextField(blank=True)
    direction = models.CharField(max_length=10, choices=DIRECTION, default="outbound")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# ------------------------------------------------------------------ Targets
class Target(models.Model):
    TYPES = [("revenue", "Revenue"), ("leads", "Leads"), ("conversions", "Conversions")]
    name = models.CharField(max_length=150)
    target_type = models.CharField(max_length=20, choices=TYPES, default="revenue")
    value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


class TargetAssignment(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey("accounts.Team", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("hr.Department", on_delete=models.SET_NULL, null=True, blank=True)


# ------------------------------------------------------------------ Proposals
class Proposal(models.Model):
    STATUS = [
        ("draft", "Draft"), ("sent", "Sent"), ("accepted", "Accepted"),
        ("rejected", "Rejected"), ("revised", "Revised"), ("expired", "Expired"),
    ]
    # Versioning: all versions of one proposal share `number`; `version` differs.
    # `parent` points to the version it was revised from; `is_current` flags latest.
    number = models.CharField(max_length=30, blank=True, db_index=True)
    version = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="revisions")
    is_current = models.BooleanField(default=True)

    title = models.CharField(max_length=200)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Money breakdown (all derived from items + tax_percent via recompute()).
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)        # gross, before discount
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Audit trail.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals_sent")
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number or '—'} v{self.version} · {self.title}"

    @property
    def reference(self):
        return f"{self.number} v{self.version}" if self.number else self.title

    def recompute(self):
        """Roll up items into subtotal/discount/tax/total."""
        from decimal import Decimal
        items = list(self.items.all())
        subtotal = sum((Decimal(i.quantity or 0) * Decimal(i.unit_price or 0) for i in items), Decimal("0"))
        taxable = sum((Decimal(i.amount or 0) for i in items), Decimal("0"))   # already net of line discounts
        tax_amount = (taxable * Decimal(self.tax_percent or 0) / Decimal("100")).quantize(Decimal("0.01"))
        self.subtotal = subtotal
        self.discount_total = (subtotal - taxable).quantize(Decimal("0.01"))
        self.tax_amount = tax_amount
        self.total = (taxable + tax_amount).quantize(Decimal("0.01"))
        self.save(update_fields=["subtotal", "discount_total", "tax_amount", "total"])

    def assign_number(self):
        """Give a brand-new proposal a professional reference (PRO-YYYY-####)."""
        if not self.number and self.pk:
            from django.utils import timezone
            self.number = f"PRO-{timezone.now().year}-{self.pk:04d}"
            self.save(update_fields=["number"])


class ProposalItem(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent off this line
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)   # net = qty*price*(1-discount%)

    def save(self, *args, **kwargs):
        from decimal import Decimal
        q, u, d = Decimal(self.quantity or 0), Decimal(self.unit_price or 0), Decimal(self.discount or 0)
        self.amount = (q * u * (Decimal("1") - d / Decimal("100"))).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)


# ------------------------------------------------------------------ Attachments
class Attachment(models.Model):
    file = models.FileField(upload_to="attachments/%Y/%m/")
    name = models.CharField(max_length=200, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    ticket = models.ForeignKey("support.Ticket", on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)


# ---- KPI / Metric Engine (PART 6) -----------------------------------------
# Generic, admin-configurable KPIs so product-specific metrics (nodes sold,
# lots traded, meetings, students, units sold, deposits…) need NO code per
# business — the spec's "nothing hardcoded" principle. Revenue is intentionally
# OUT of scope: it stays in sales.Revenue (single source of truth). Rollup is
# aggregation-aware (see reports/metrics.py): sum/count add up the org tree,
# average is count-weighted, latest is a snapshot (not summed).
class MetricDefinition(models.Model):
    AGG = [("sum", "Sum"), ("count", "Count"), ("average", "Average"), ("latest", "Latest")]
    CATEGORY = [("growth", "Growth"), ("activity", "Activity"), ("other", "Other")]
    SOURCE = [("manual", "Manual entry"), ("derived", "Derived from CRM data")]
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    # derived metrics read existing CRM signals instead of manual entries
    DERIVED = [
        ("", "—"),
        ("lead_activity:meeting", "Meetings logged (Lead Activity)"),
        ("lead_activity:call", "Calls logged (Lead Activity)"),
        ("lead:converted", "Leads converted"),
    ]
    name = models.CharField(max_length=120)
    key = models.SlugField(max_length=140, unique=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True, related_name="metrics")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)                 # "$", "GB", "count", "lots"
    aggregation = models.CharField(max_length=20, choices=AGG, default="sum")
    category = models.CharField(max_length=20, choices=CATEGORY, default="activity")
    source = models.CharField(max_length=20, choices=SOURCE, default="manual")
    derived_key = models.CharField(max_length=40, choices=DERIVED, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.key:
            from django.utils.text import slugify
            base = slugify(self.name) or "metric"
            k, i = base, 1
            while MetricDefinition.objects.exclude(pk=self.pk).filter(key=k).exists():
                i += 1
                k = f"{base}-{i}"
            self.key = k
        super().save(*args, **kwargs)


class MetricEntry(models.Model):
    """One recorded value for a manual metric, attributed to an employee."""
    metric = models.ForeignKey(MetricDefinition, on_delete=models.CASCADE, related_name="entries")
    employee = models.ForeignKey("hr.Employee", on_delete=models.CASCADE, related_name="metric_entries")
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
    date = models.DateField()

    class Meta:
        verbose_name_plural = "Metric entries"
        ordering = ["-date"]


# ---- New AUM Engine (PART 11) ---------------------------------------------
# Tracks deposits & withdrawals per RM's client so the system can separate
# Existing AUM, New Deposits, Withdrawals and Net New AUM (= deposits −
# withdrawals). Rolled up the org tree in reports/aum.py — visible to RM/TL/
# Sales Manager/Business Head.
class AumEntry(models.Model):
    TYPES = [("deposit", "Deposit"), ("withdrawal", "Withdrawal")]
    employee = models.ForeignKey("hr.Employee", on_delete=models.CASCADE, related_name="aum_entries")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)  # per-business AUM
    entry_type = models.CharField(max_length=12, choices=TYPES, default="deposit")
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    external_id = models.CharField(max_length=80, blank=True, db_index=True)  # idempotent external sync key
    note = models.CharField(max_length=200, blank=True)
    date = models.DateField()

    class Meta:
        verbose_name_plural = "AUM entries"
        ordering = ["-date"]


# ---- Business Contribution Engine (PART 12) -------------------------------
# Captures the revenue/loss components of a client so Net Business Contribution
# can be derived. The formula is admin-configurable (ContributionWeight) — the
# CRM does not hardcode it. Computation/rollup live in reports/contribution.py.
class ContributionEntry(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey("hr.Employee", on_delete=models.CASCADE, related_name="contributions")
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)
    deposit = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    trading_loss = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    brokerage = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    staking = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    other = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    date = models.DateField()

    class Meta:
        verbose_name_plural = "Contribution entries"
        ordering = ["-date"]


class ContributionWeight(models.Model):
    """Single global config: the multiplier applied to each component when
    computing Net Business Contribution (admin-defined, not hardcoded).
    Default: revenue parts +1, trading loss −1, deposit excluded (0)."""
    deposit = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    trading_loss = models.DecimalField(max_digits=6, decimal_places=2, default=-1)
    brokerage = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    insurance = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    staking = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    other = models.DecimalField(max_digits=6, decimal_places=2, default=1)

    COMPONENTS = ["deposit", "trading_loss", "brokerage", "insurance", "staking", "other"]

    def __str__(self):
        return "Contribution formula"
