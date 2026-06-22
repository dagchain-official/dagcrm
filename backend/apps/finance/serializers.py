from rest_framework import serializers

from .models import Commission, Expense


class ExpenseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.department_name", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "department", "department_name", "amount", "expense_type",
                  "description", "date"]


class CommissionSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = Commission
        fields = ["id", "partner_name", "amount", "business", "business_name", "date"]
