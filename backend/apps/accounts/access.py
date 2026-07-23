"""Central access-control config for the 3-layer permission system.

Layer 1  Role        -> default dashboard + which modules appear
Layer 2  Business    -> which businesses' data a user can see (UserPermission)
Layer 3  Module CRUD -> per role+module view/create/edit/delete (ModulePermission)
"""

# ---- Roles (document hierarchy) ----
ROLES = [
    "Super Admin", "Business Head", "Sales Director", "Sales Manager", "Team Leader",
    "Sales Executive", "Support", "HR", "Finance",
]

# Roles that see ALL data (company-wide), bypass business scoping.
MANAGER_ROLES = {"Super Admin", "Business Head"}

# Who may assign targets is a PERMISSION ("assign-targets" in the matrix), not a
# fixed list of roles — grant it to a Sales Manager or Team Leader and they can
# set targets too. This set is only the DEFAULT the matrix is seeded with, and
# the fallback for a role that has no matrix row yet.
# Whoever holds it, the reach is the same: their own team, downwards. Only the
# Super Admin assigns across the whole company.
TARGET_ASSIGNER_ROLES = {"Super Admin", "Business Head", "Sales Director"}

# Roles that see ALL data (company-wide), bypass business scoping.
ASSIGNABLE_LEAD_ROLES = ["Sales Manager", "Team Leader", "Sales Executive"]

# Roles that may ASSIGN/DISTRIBUTE leads to others. Sales Executive is the last
# rung — it works its own leads but cannot assign to anyone.
LEAD_ASSIGNER_ROLES = {"Super Admin", "Business Head", "Sales Director", "Sales Manager", "Team Leader"}


def can_assign_leads(user):
    if getattr(user, "is_superuser", False):
        return True
    return getattr(getattr(user, "role", None), "name", None) in LEAD_ASSIGNER_ROLES

# ---- Role -> org level -------------------------------------------------
# The org level is DERIVED from the role, never typed on the form: role name ->
# (level name, level order). 1 = top of the org. Support/HR/Finance sit outside
# the sales ladder, so they share the bottom rung.
ROLE_TO_LEVEL = {
    "Super Admin":     ("Business Head", 1),
    "Business Head":   ("Business Head", 1),
    "Sales Director":  ("Sales Director", 2),
    "Sales Manager":   ("Sales Manager", 3),
    "Team Leader":     ("Team Leader", 4),
    "Sales Executive": ("Relationship Manager", 5),
    "Support":         ("Support", 6),
    "HR":              ("HR", 6),
    "Finance":         ("Finance", 6),
}

# Which dashboard each role lands on (frontend route key).
ROLE_DASHBOARD = {
    "Super Admin": "admin",
    "Business Head": "admin",
    "Sales Director": "admin",
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
    # FX Artha and DAGChain are split per sub-page so each can be granted/denied
    # separately (the sidebar item + its endpoint use these keys).
    "fxartha", "fxartha-traders", "fxartha-lots",
    "dagchain", "dagchain-users", "dagchain-nodes",
    # capability modules — see ACTION_MODULES
    "assign-targets",
]

# Modules that aren't a CRUD screen but a single capability. Only `create` is
# meaningful on these, and the Permission Matrix shows one toggle instead of four.
ACTION_MODULES = {"assign-targets"}


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
    "Sales Director": {
        **_full(_split("leads lead-activities opportunities proposals customers communications targets "
                       "metric-entries aum-entries contribution-entries teams")),
        **_view(_split("revenues products businesses lead-sources tickets reports users "
                       "metric-definitions employees fxartha fxartha-traders fxartha-lots dagchain dagchain-users dagchain-nodes")),
        "leaves": "vce", "leave-types": "v",
        "assign-targets": "c",
    },
    "Sales Manager": {
        **_full(_split("leads lead-activities opportunities proposals customers communications targets "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("revenues products businesses lead-sources tickets reports teams users "
                       "metric-definitions fxartha fxartha-traders fxartha-lots dagchain dagchain-users dagchain-nodes")),
        # team leave management
        "leaves": "vce", "leave-types": "v", "employees": "v",
        # may set targets — for their own team only (see can_assign_to)
        "assign-targets": "c",
    },
    "Team Leader": {
        **_full(_split("leads lead-activities opportunities proposals customers communications "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("targets tickets reports metric-definitions fxartha fxartha-traders fxartha-lots dagchain dagchain-users dagchain-nodes")),
        # team leave management
        "leaves": "vce", "leave-types": "v", "employees": "v",
        # may set targets — for their own team only (see can_assign_to)
        "assign-targets": "c",
    },
    "Sales Executive": {
        **_full(_split("leads lead-activities opportunities proposals customers communications "
                       "metric-entries aum-entries contribution-entries")),
        **_view(_split("tickets businesses products metric-definitions fxartha fxartha-traders fxartha-lots dagchain dagchain-users dagchain-nodes")),
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
        # read-only lookups the HR forms need: roles (New Employee -> Role
        # dropdown), users, and businesses/products for the incentive-rule form
        **_view(_split("roles users reports businesses products")),
    },
    "Finance": {
        **_full(_split("revenues expenses commissions payrolls cost-categories employee-costs "
                       "target-multipliers aum-entries contribution-entries contribution-weights")),
        **_view(_split("reports businesses employees fxartha fxartha-traders fxartha-lots dagchain dagchain-users dagchain-nodes")),
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
    "DagChainProfileViewSet": "dagchain-users",
    "DagChainNodeViewSet": "dagchain-nodes",
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


def subordinate_user_ids(user, include_self=False):
    """All user ids in this user's management subtree (via Employee.manager chain)."""
    from apps.hr.models import Employee
    reports = {}
    for e in Employee.objects.values("user_id", "manager_id"):
        reports.setdefault(e["manager_id"], []).append(e["user_id"])
    out = set()
    if include_self:
        out.add(user.id)
    stack = [user.id]
    while stack:
        mid = stack.pop()
        for uid in reports.get(mid, []):
            if uid and uid not in out:
                out.add(uid)
                stack.append(uid)
    return out


def can_assign_targets(user):
    """Whether the user may assign targets at all — driven by the
    "assign-targets" permission so it can be granted to any role from the
    Permission Matrix. A role with no matrix row yet falls back to the default
    set, so behaviour never silently disappears."""
    if getattr(user, "is_superuser", False):
        return True
    perms = role_permissions(user)
    if "assign-targets" in perms:
        return bool(perms["assign-targets"].get("create"))
    return getattr(getattr(user, "role", None), "name", None) in TARGET_ASSIGNER_ROLES


def can_assign_to(actor, target_user_id, allow_self=False):
    """How far an assigner reaches: the Super Admin covers the whole company;
    everyone else only their own subtree — you can set targets for the people
    below you, never for a peer or someone above you.

    `allow_self` is for team/business targets: the roll-up legitimately includes
    the leader themselves, and refusing that would block a manager from setting
    their own team's number. An INDIVIDUAL target still has to go downwards.
    """
    if getattr(actor, "is_superuser", False):
        return True
    if getattr(getattr(actor, "role", None), "name", None) == "Super Admin":
        return True
    if not can_assign_targets(actor):
        return False
    return target_user_id in subordinate_user_ids(actor, include_self=allow_self)


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
