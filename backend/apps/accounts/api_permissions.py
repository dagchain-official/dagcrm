from rest_framework.permissions import BasePermission, SAFE_METHODS

from .access import VIEWSET_MODULE, role_permissions

# HTTP method -> required permission action
METHOD_ACTION = {
    "GET": "view", "HEAD": "view", "OPTIONS": "view",
    "POST": "create", "PUT": "edit", "PATCH": "edit", "DELETE": "delete",
}


class IsAdminView(BasePermission):
    """Only managers/superuser (company-wide view) may manage permissions."""

    message = "Only administrators can manage permissions."

    def has_permission(self, request, view):
        from .access import is_admin_view
        return is_admin_view(request.user)


class ModuleAccess(BasePermission):
    """Layer 3 — enforce role+module CRUD permissions on every managed viewset.

    Views not present in VIEWSET_MODULE (auth, reports, custom APIViews) are
    left to their own permission_classes / IsAuthenticated.
    """

    message = "You don't have permission for this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        module = VIEWSET_MODULE.get(type(view).__name__)
        if module is None:
            return True  # not a permission-managed module

        action = METHOD_ACTION.get(request.method, "view")
        perms = role_permissions(user).get(module, {})
        return bool(perms.get(action, False))
