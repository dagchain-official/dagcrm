"""Central access-control config for the 3-layer permission system.

Layer 1  Role        -> default dashboard + which modules appear
Layer 2  Business    -> which businesses' data a user can see (UserPermission)
Layer 3  Module CRUD -> per role+module view/create/edit/delete (ModulePermission)
"""

# ---- Roles (document hierarchy) ----
ROLES = [
    "Super Admin", "Business Head", "Sales Manager", "Team Leader",
    "Sales Executive", "Support", "HR", "Finance",
]

# Roles that see ALL data (company-wide), bypass business scoping.
MANAGER_ROLES = {"Super Admin", "Business Head"}

# Roles that leads can be assigned to (sales chain only).
ASSIGNABLE_LEAD_ROLES = ["Sales Manager", "Team Leader", "Sales Executive"]

# Roles that may ASSIGN/DISTRIBUTE leads to others. Sales Executive is the last
# rung — it works its own leads but cannot assign to anyone.
LEAD_ASSIGNER_ROLES = {"Super Admin", "Business Head", "Sales Manager", "Team Leader"}


def can_assign_leads(user):
    if getattr(user, "is_superuser", False):
        return True
    return getattr(getattr(user, "role", None), "name", None) in LEAD_ASSIGNER_ROLES

# Which dashboard each role lands on (frontend route key).
ROLE_DASHBOARD = {
    "Super Admin": "admin",
    "Business Head": "admin",
    "Sales Manager": "sales-manager",
    "Team Leader": "team-leader",
    "Sales Executive": "sales-exec",
    "Support": "support",
    "HR": "hr",
    "Finance": "finance",
}

# ---- Every CRUD module key (matches frontend resource + viewset map) ----
MODULES = [
    "leads", "lead-activities", "opportunities", "proposals", "customers", "communications",
    "targets", "metric-definitions", "metric-entries", "aum-entries",
    "contribution-entries", "contribution-weights",
    "revenues", "businesses", "products", "lead-sources", "tickets",
    "employees", "departments", "hierarchy-levels", "attendance", "employee-activities", "leaves",
    "leave-types", "payrolls", "incentives", "incentive-rules", "cost-categories", "employee-costs",
    "target-multipliers", "performance-weights", "incentive-slabs", "activity-incentives",
    "formula-rules", "expenses", "commissions", "users", "roles", "teams", "reports",
]


def _split(s):
    return s.split()


# Compact matrix. Value = action letters: v=view c=create e=edit d=delete.
# "vced" = full access, "v" = view only. Missing module = no access.
def _full(keys):
    return {m: "vced" for m in keys}


def _view(keys):
    return {m: "v" for m in keys}


ROLE_MATRIX = {
    "Super Admin": _full(MODULES),
    "Business Head": _full(MODULES),
    "Sales Manager": {
        **_full(_split("leads lead-activities opportunities proposals customers communications targets "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("revenues products businesses lead-sources tickets reports teams users metric-definitions")),
        # team leave management
        "leaves": "vce", "leave-types": "v", "employees": "v",
    },
    "Team Leader": {
        **_full(_split("leads lead-activities opportunities proposals customers communications "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("targets tickets reports metric-definitions")),
        # team leave management
        "leaves": "vce", "leave-types": "v", "employees": "v",
    },
    "Sales Executive": {
        **_full(_split("leads lead-activities opportunities proposals customers communications "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("tickets businesses products metric-definitions")),
    },
    "Support": {
        **_full(_split("tickets")),
        **_view(_split("customers communications reports")),
    },
    "HR": {
        **_full(_split("employees departments hierarchy-levels attendance employee-activities leaves "
                       "leave-types payrolls incentives incentive-rules cost-categories employee-costs "
                       "target-multipliers performance-weights incentive-slabs activity-incentives "
                       "formula-rules")),
        # businesses + products are read-only lookups the incentive-rule form needs
        **_view(_split("users reports businesses products")),
    },
    "Finance": {
        **_full(_split("revenues expenses commissions payrolls cost-categories employee-costs "
                       "target-multipliers aum-entries contribution-entries contribution-weights")),
        **_view(_split("reports businesses employees")),
    },
}

# ---- Viewset class name -> module key (drives Layer 3 enforcement) ----
VIEWSET_MODULE = {
    "LeadViewSet": "leads",
    "LeadActivityViewSet": "lead-activities",
    "LeadInterestViewSet": "leads",
    "OpportunityViewSet": "opportunities",
    "ProposalViewSet": "proposals",
    "CustomerViewSet": "customers",
    "CustomerProductViewSet": "customers",
    "CommunicationViewSet": "communications",
    "TargetViewSet": "targets",
    "TargetAssignmentViewSet": "targets",
    "MetricDefinitionViewSet": "metric-definitions",
    "MetricEntryViewSet": "metric-entries",
    "AumEntryViewSet": "aum-entries",
    "ContributionEntryViewSet": "contribution-entries",
    "ContributionWeightViewSet": "contribution-weights",
    "RevenueViewSet": "revenues",
    "BusinessViewSet": "businesses",
    "ProductViewSet": "products",
    "LeadSourceViewSet": "lead-sources",
    "TicketViewSet": "tickets",
    "TicketCommentViewSet": "tickets",
    "EmployeeViewSet": "employees",
    "DepartmentViewSet": "departments",
    "HierarchyLevelViewSet": "hierarchy-levels",
    "CostCategoryViewSet": "cost-categories",
    "EmployeeCostViewSet": "employee-costs",
    "AttendanceViewSet": "attendance",
    "EmployeeActivityViewSet": "employee-activities",
    "LeaveViewSet": "leaves",
    "LeaveTypeViewSet": "leave-types",
    "PayrollViewSet": "payrolls",
    "IncentiveViewSet": "incentives",
    "IncentiveRuleViewSet": "incentive-rules",
    "TargetMultiplierViewSet": "target-multipliers",
    "PerformanceWeightViewSet": "performance-weights",
    "IncentiveSlabViewSet": "incentive-slabs",
    "ActivityIncentiveViewSet": "activity-incentives",
    "FormulaRuleViewSet": "formula-rules",
    "ExpenseViewSet": "expenses",
    "CommissionViewSet": "commissions",
    "UserViewSet": "users",
    "RoleViewSet": "roles",
    "TeamViewSet": "teams",
    "TeamMemberViewSet": "teams",
    "UserPermissionViewSet": "users",
}


def is_admin_view(user):
    """True if user sees company-wide data (managers/superuser)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(user.role, "name", None) in MANAGER_ROLES


def can_manage_all_leaves(user):
    """HR + top management see/approve every leave."""
    return is_admin_view(user) or getattr(user.role, "name", None) == "HR"


def role_permissions(user):
    """Return {module: {view,create,edit,delete}} for the user's role."""
    if user.is_superuser:
        return {m: {"view": True, "create": True, "edit": True, "delete": True} for m in MODULES}
    from .models import ModulePermission
    out = {}
    qs = ModulePermission.objects.filter(role=user.role) if user.role_id else []
    for p in qs:
        out[p.module] = {"view": p.can_view, "create": p.can_create,
                         "edit": p.can_edit, "delete": p.can_delete}
    return out


def allowed_business_ids(user):
    """Layer 2: business ids a user may see. None == all."""
    if is_admin_view(user):
        return None
    from .models import UserPermission
    ids = list(
        UserPermission.objects.filter(user=user, can_view=True, business__isnull=False)
        .values_list("business_id", flat=True)
    )
    return ids or None  # no explicit grants -> see all (don't break)
