from rest_framework import viewsets

from apps.accounts.scoping import BusinessScopedMixin

from .models import Revenue
from .serializers import RevenueSerializer


class RevenueViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = Revenue.objects.select_related("customer", "business", "product").all().order_by("-created_at")
    serializer_class = RevenueSerializer
    filterset_fields = ["business", "product", "customer"]
    search_fields = ["customer__name"]
