from django.conf import settings
from django.db import models


# ------------------------------------------------------------------ Business
class Business(models.Model):
    """FX Artha, DAGChain, DAGGPT, DAGDB, Energy DAO, DAG Army."""

    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS = [("active", "Active"), ("inactive", "Inactive")]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
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
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_leads")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_leads")
    status = models.CharField(max_length=20, choices=STATUS, default="new")
    score = models.PositiveIntegerField(default=0)  # AI lead score (0-100)
    created_at = models.DateTimeField(auto_now_add=True)

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
    STATUS = [("draft", "Draft"), ("sent", "Sent"), ("accepted", "Accepted"), ("rejected", "Rejected")]
    title = models.CharField(max_length=200)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def recompute(self):
        self.total = sum((i.amount for i in self.items.all()), 0)
        self.save(update_fields=["total"])


class ProposalItem(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.amount = (self.quantity or 0) * (self.unit_price or 0)
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
