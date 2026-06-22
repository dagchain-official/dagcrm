from rest_framework import serializers

from .models import Revenue


class RevenueSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Revenue
        fields = ["id", "customer", "customer_name", "business", "business_name",
                  "product", "product_name", "gross_revenue", "commission",
                  "net_revenue", "created_at"]
        read_only_fields = ["net_revenue", "created_at"]
