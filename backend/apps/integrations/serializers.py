from rest_framework import serializers

from .models import PLATFORMS, DagChainNode, DagChainProfile, IntegrationConnection, IntegrationLog


class DagChainProfileSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    rm = serializers.CharField(source="customer.assigned_to.name", read_only=True)

    class Meta:
        model = DagChainProfile
        fields = ["id", "customer", "customer_name", "rm", "external_id", "display_name",
                  "email", "wallet_address", "user_type", "status", "email_verified",
                  "kyc_status", "social_provider", "dgc_balance", "fuel_wallet_usd",
                  "referral_code", "referral_count", "total_referral_earnings",
                  "validator_nodes_count", "storage_nodes_count", "login_count",
                  "joined_at", "synced_at"]


class DagChainNodeSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    rm = serializers.CharField(source="customer.assigned_to.name", read_only=True)

    class Meta:
        model = DagChainNode
        fields = ["id", "customer", "customer_name", "rm", "external_id", "kind", "node_key",
                  "package", "purchase_price", "currency", "status", "payment_status",
                  "uptime", "blocks_validated", "rewards_earned", "pending_rewards",
                  "claimed_rewards", "effective_apy", "capacity", "is_staked",
                  "staked_amount", "staking_requirement", "opened_at", "synced_at"]


class IntegrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationLog
        fields = ["id", "status", "message", "created_at"]


class IntegrationConnectionSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)
    source_name = serializers.CharField(read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    is_poll = serializers.SerializerMethodField()
    config_fields = serializers.SerializerMethodField()
    webhook_url = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationConnection
        fields = ["id", "platform", "business", "business_name", "name", "label",
                  "source_name", "is_poll", "status", "webhook_secret", "webhook_url",
                  "config", "config_fields", "auto_assign", "total_leads",
                  "last_lead_at", "recent_logs", "created_at"]
        read_only_fields = ["webhook_secret", "total_leads", "last_lead_at", "created_at"]

    def get_is_poll(self, obj):
        return bool(PLATFORMS.get(obj.platform, {}).get("poll"))

    def get_config_fields(self, obj):
        return PLATFORMS.get(obj.platform, {}).get("fields", [])

    def get_webhook_url(self, obj):
        request = self.context.get("request")
        base = request.build_absolute_uri("/").rstrip("/") if request else ""
        # id in the path so each (platform, business) connection has a distinct URL
        return f"{base}/api/integrations/{obj.platform}/{obj.id}/webhook/?key={obj.webhook_secret}"

    def get_recent_logs(self, obj):
        return IntegrationLogSerializer(obj.logs.all()[:5], many=True).data
