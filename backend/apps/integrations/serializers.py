from rest_framework import serializers

from .models import PLATFORMS, IntegrationConnection, IntegrationLog


class IntegrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationLog
        fields = ["id", "status", "message", "created_at"]


class IntegrationConnectionSerializer(serializers.ModelSerializer):
    label = serializers.CharField(read_only=True)
    source_name = serializers.CharField(read_only=True)
    config_fields = serializers.SerializerMethodField()
    webhook_url = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationConnection
        fields = ["id", "platform", "label", "source_name", "status", "webhook_secret",
                  "webhook_url", "config", "config_fields", "auto_assign", "total_leads",
                  "last_lead_at", "recent_logs", "created_at"]
        read_only_fields = ["webhook_secret", "total_leads", "last_lead_at", "created_at"]

    def get_config_fields(self, obj):
        return PLATFORMS.get(obj.platform, {}).get("fields", [])

    def get_webhook_url(self, obj):
        request = self.context.get("request")
        base = request.build_absolute_uri("/").rstrip("/") if request else ""
        return f"{base}/api/integrations/{obj.platform}/webhook/?key={obj.webhook_secret}"

    def get_recent_logs(self, obj):
        return IntegrationLogSerializer(obj.logs.all()[:5], many=True).data
