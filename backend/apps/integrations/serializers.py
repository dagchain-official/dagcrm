from rest_framework import serializers

from .models import PLATFORMS, IntegrationConnection, IntegrationLog


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
