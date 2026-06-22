from rest_framework import viewsets

from apps.accounts.scoping import BusinessScopedMixin

from .models import Commission, Expense
from .serializers import CommissionSerializer, ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related("department").all()
    serializer_class = ExpenseSerializer
    filterset_fields = ["department", "expense_type"]


class CommissionViewSet(BusinessScopedMixin, viewsets.ModelViewSet):
    queryset = Commission.objects.select_related("business").all()
    serializer_class = CommissionSerializer
    filterset_fields = ["business"]
    search_fields = ["partner_name"]
