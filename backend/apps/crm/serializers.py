from rest_framework import serializers

from .models import (
    Attachment, AumEntry, Business, Communication, ContributionEntry, ContributionWeight,
    Customer, CustomerProduct, Lead, LeadActivity, LeadInterest, LeadSource, MetricDefinition,
    MetricEntry, Opportunity, Product, Proposal, ProposalItem, Target, TargetAssignment,
)


class ProposalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalItem
        fields = ["id", "description", "quantity", "unit_price", "discount", "amount"]
        read_only_fields = ["amount"]


class ProposalSerializer(serializers.ModelSerializer):
    items = ProposalItemSerializer(many=True, required=False)
    contact = serializers.SerializerMethodField()
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)
    reference = serializers.CharField(read_only=True)
    revision_count = serializers.SerializerMethodField()

    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = Proposal
        fields = ["id", "number", "version", "parent", "is_current", "reference", "revision_count",
                  "title", "lead", "lead_name", "customer", "customer_name", "contact",
                  "business", "business_name", "status", "valid_until", "notes",
                  "tax_percent", "subtotal", "discount_total", "tax_amount", "total",
                  "item_count", "items", "sent_at", "accepted_at", "rejected_at", "created_at"]
        read_only_fields = ["number", "version", "parent", "is_current", "subtotal",
                            "discount_total", "tax_amount", "total", "sent_at",
                            "accepted_at", "rejected_at", "created_at"]

    def get_contact(self, obj):
        if obj.customer_id and obj.customer:
            return obj.customer.name
        if obj.lead_id and obj.lead:
            return obj.lead.name
        return "—"

    def get_revision_count(self, obj):
        # how many versions exist under this proposal number
        if not obj.number:
            return 1
        return Proposal.objects.filter(number=obj.number).count()

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        proposal = Proposal.objects.create(**validated_data)
        for it in items:
            ProposalItem.objects.create(proposal=proposal, **it)
        proposal.recompute()
        proposal.assign_number()
        return proposal

    def update(self, instance, validated_data):
        # Professionalism: once a proposal leaves draft it is locked — edits must
        # go through a new version (the `revise` action), preserving the audit trail.
        if instance.status != "draft":
            raise serializers.ValidationError(
                "Only draft proposals can be edited. Create a revision to change a sent/accepted proposal.")
        items = validated_data.pop("items", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for it in items:
                ProposalItem.objects.create(proposal=instance, **it)
        instance.recompute()
        return instance


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
        fields = ["id", "business", "business_name", "name", "product_type",
                  "price", "revenue_type", "status"]


class BusinessSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Business
        fields = ["id", "name", "description", "status", "products",
                  "product_count", "created_at"]


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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Super admin / business head see everything. Assigned employees (RMs)
        # must NOT see the phone number — email & rest stay visible. They still
        # call/WhatsApp via the system (number is used server-side only).
        from apps.accounts.access import is_admin_view
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not is_admin_view(user):
            data["phone"] = ""          # hidden from employees
            data["phone_hidden"] = True
        return data

    def update(self, instance, validated_data):
        # employees can't change/blank the number (their view sends it empty)
        from apps.accounts.access import is_admin_view
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not is_admin_view(user):
            validated_data.pop("phone", None)
        return super().update(instance, validated_data)


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


# ---- KPI / Metric Engine (PART 6) ----------------------------------------
class MetricDefinitionSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = MetricDefinition
        fields = ["id", "name", "key", "business", "business_name", "product", "product_name",
                  "unit", "aggregation", "category", "source", "derived_key", "status", "label"]
        read_only_fields = ["key"]

    def get_label(self, obj):
        scope = obj.business.name if obj.business_id else "All businesses"
        return f"{obj.name} · {scope}"

    def validate(self, attrs):
        source = attrs.get("source") or getattr(self.instance, "source", "manual")
        derived = attrs.get("derived_key") or getattr(self.instance, "derived_key", "")
        if source == "derived" and not derived:
            raise serializers.ValidationError(
                {"derived_key": "Pick a CRM signal when source is 'Derived'."})
        if source == "manual":
            attrs["derived_key"] = ""
        return attrs


class MetricEntrySerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source="metric.name", read_only=True)
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    unit = serializers.CharField(source="metric.unit", read_only=True)

    class Meta:
        model = MetricEntry
        fields = ["id", "metric", "metric_name", "unit", "employee", "employee_name",
                  "value", "customer", "lead", "note", "date"]

    def validate_metric(self, metric):
        if metric.source == "derived":
            raise serializers.ValidationError(
                "This is a derived metric — its values come from CRM data, not manual entry.")
        return metric


class AumEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = AumEntry
        fields = ["id", "employee", "employee_name", "customer", "customer_name",
                  "business", "business_name", "entry_type", "amount", "note", "date"]


class ContributionEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = ContributionEntry
        fields = ["id", "customer", "customer_name", "employee", "employee_name",
                  "business", "business_name", "deposit", "trading_loss", "brokerage",
                  "insurance", "staking", "other", "date"]


class ContributionWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionWeight
        fields = ["id", "deposit", "trading_loss", "brokerage", "insurance", "staking", "other"]
