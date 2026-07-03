from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.Model):
    """Super Admin, Business Head, Regional Manager, Team Leader, RM, Support, HR, Finance."""

    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("status", "active")
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    STATUS = [("active", "Active"), ("inactive", "Inactive"), ("suspended", "Suspended")]

    employee_id = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    status = models.CharField(max_length=20, choices=STATUS, default="active")

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class EmailAccount(models.Model):
    """A 'from' business mailbox a user can send lead emails through.
    Each user may configure multiple accounts (different businesses / addresses)
    and pick one when emailing a lead. Real delivery uses the stored SMTP creds."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_accounts")
    label = models.CharField(max_length=80)                 # e.g. "FX Artha Sales"
    from_name = models.CharField(max_length=120, blank=True)  # display name on the email
    from_email = models.EmailField()
    smtp_host = models.CharField(max_length=120, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=190, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)  # app password
    use_tls = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "label"]

    def __str__(self):
        return f"{self.label} <{self.from_email}>"


class UserPermission(models.Model):
    """Per business / product access matrix for a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="permissions")
    business = models.ForeignKey("crm.Business", on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey("crm.Product", on_delete=models.CASCADE, null=True, blank=True)
    can_view = models.BooleanField(default=True)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "business", "product")


class ModulePermission(models.Model):
    """Layer 3 — per role + module CRUD permissions (the Permission Matrix)."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="module_permissions")
    module = models.CharField(max_length=40)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("role", "module")

    def __str__(self):
        return f"{self.role} · {self.module}"


class Team(models.Model):
    name = models.CharField(max_length=120)
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="led_teams")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")

    class Meta:
        unique_together = ("team", "user")


class TeamRequest(models.Model):
    """A Sales Manager cannot pick their own team members directly — they raise a
    request for a person, which a higher authority (Sales Director / Business Head /
    Admin) approves or rejects. On approval the person is added to the team."""
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_requests")
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requested_in")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="join_requests")
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="team_decisions")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requested_by} wants {self.member} ({self.status})"
