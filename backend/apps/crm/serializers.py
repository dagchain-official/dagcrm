from rest_framework import serializers

from .models import (
    Attachment, Business, Communication, Customer, CustomerProduct, Lead, LeadActivity,
    LeadInterest, LeadSource, Opportunity, Product, Target, TargetAssignment,
)


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.name", read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "file", "file_url", "name", "customer", "ticket",
                  "uploaded_by", "uploaded_by_name", "created_at"]
        read_only_fields = ["created_at", "name"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url if obj.file else None
        return request.build_absolute_uri(url) if request and url else url


class ProductSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "business", "business_name", "name", "status"]


class BusinessSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Business
        fields = ["id", "name", "description", "products", "product_count", "created_at"]


class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = "__all__"


class LeadInterestSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = LeadInterest
        fields = ["id", "lead", "business", "business_name", "product", "product_name"]


class LeadActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    lead_name = serializers.CharField(source="lead.name", read_only=True)

    class Meta:
        model = LeadActivity
        fields = ["id", "lead", "lead_name", "user", "user_name", "activity_type", "remarks",
                  "followup_date", "next_action", "created_at"]
        read_only_fields = ["created_at"]


class LeadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    assigned_name = serializers.CharField(source="assigned_to.name", read_only=True)
    interests = LeadInterestSerializer(many=True, read_only=True)
    activity_count = serializers.IntegerField(source="activities.count", read_only=True)

    class Meta:
        model = Lead
        fields = ["id", "lead_code", "name", "email", "phone", "country", "source",
                  "source_name", "assigned_to", "assigned_name", "created_by", "status",
                  "score", "interests", "activity_count", "created_at"]
        read_only_fields = ["created_at", "score"]


class OpportunitySerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    assigned_name = serializers.CharField(source="assigned_to.name", read_only=True)

    class Meta:
        model = Opportunity
        fields = ["id", "lead", "lead_name", "product", "product_name", "assigned_to",
                  "assigned_name", "stage", "expected_revenue", "status", "created_at"]
        read_only_fields = ["created_at"]


class CustomerProductSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = CustomerProduct
        fields = ["id", "customer", "business", "business_name", "product", "product_name", "status"]


class CustomerSerializer(serializers.ModelSerializer):
    products = CustomerProductSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "country", "lead", "products", "created_at"]
        read_only_fields = ["created_at"]


class CommunicationSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    contact = serializers.SerializerMethodField()

    class Meta:
        model = Communication
        fields = ["id", "lead", "lead_name", "customer", "customer_name", "contact",
                  "channel", "message", "direction", "created_at"]
        read_only_fields = ["created_at"]

    def get_contact(self, obj):
        if obj.customer_id and obj.customer:
            return obj.customer.name
        if obj.lead_id and obj.lead:
            return obj.lead.name
        return "—"


class TargetAssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = TargetAssignment
        fields = ["id", "target", "user", "user_name", "team", "department"]


class TargetSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    assignments = TargetAssignmentSerializer(many=True, read_only=True)
    achieved = serializers.SerializerMethodField()
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model = Target
        fields = ["id", "name", "target_type", "value", "business", "business_name",
                  "start_date", "end_date", "assignments", "achieved", "progress_pct"]

    def get_achieved(self, obj):
        from django.db.models import Count, Sum
        from apps.sales.models import Revenue

        rng = {"created_at__date__gte": obj.start_date, "created_at__date__lte": obj.end_date}
        if obj.target_type == "revenue":
            qs = Revenue.objects.filter(**rng)
            if obj.business_id:
                qs = qs.filter(business_id=obj.business_id)
            return float(qs.aggregate(s=Sum("net_revenue"))["s"] or 0)
        if obj.target_type == "leads":
            return Lead.objects.filter(created_at__date__gte=obj.start_date,
                                       created_at__date__lte=obj.end_date).count()
        if obj.target_type == "conversions":
            return Lead.objects.filter(status="converted",
                                       created_at__date__gte=obj.start_date,
                                       created_at__date__lte=obj.end_date).count()
        return 0

    def get_progress_pct(self, obj):
        target = float(obj.value or 0)
        if target <= 0:
            return 0
        return round(min(100, self.get_achieved(obj) / target * 100), 1)
