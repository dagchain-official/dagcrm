from .access import allowed_business_ids


class BusinessScopedMixin:
    """Layer 2 — restrict a viewset's queryset to the user's allowed businesses.

    Set `business_scope_field` to the FK path to a Business (default "business_id").
    Managers / users without explicit grants see everything.
    """

    business_scope_field = "business_id"

    def get_queryset(self):
        qs = super().get_queryset()
        ids = allowed_business_ids(self.request.user)
        if ids is None:
            return qs
        return qs.filter(**{f"{self.business_scope_field}__in": ids})
