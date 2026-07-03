import secrets

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.api_permissions import IsAdminView

from .models import PLATFORMS, IntegrationConnection
from .serializers import IntegrationConnectionSerializer
from .services import process_webhook


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def webhook(request, platform, conn_id=None):
    """Public endpoint that external platforms POST leads to.

    GET  -> verification handshake (Meta-style hub.challenge).
    POST -> ingest leads (secret verified via ?key= or X-Webhook-Secret header).

    conn_id in the path selects a specific (platform, business) connection.
    Without it (legacy URL), the first connection for the platform is used.
    """
    if platform not in PLATFORMS:
        return Response({"detail": "Unknown platform"}, status=404)
    qs = IntegrationConnection.objects.filter(platform=platform)
    conn = qs.filter(pk=conn_id).first() if conn_id else qs.first()

    # Meta subscription verification
    if request.method == "GET":
        if (request.GET.get("hub.mode") == "subscribe"
                and conn and request.GET.get("hub.verify_token") == conn.webhook_secret):
            return HttpResponse(request.GET.get("hub.challenge", ""))
        return Response({"status": "ready", "platform": platform})

    if not conn or conn.status != "connected":
        return Response({"detail": "Integration not connected"}, status=400)

    key = request.GET.get("key") or request.headers.get("X-Webhook-Secret")
    if conn.webhook_secret and key != conn.webhook_secret:
        return Response({"detail": "Invalid webhook secret"}, status=403)

    result = process_webhook(conn, request.data)
    return Response(result)


class IntegrationConnectionViewSet(viewsets.ModelViewSet):
    """Admin-managed integration connections — one row per (platform, business)."""
    queryset = IntegrationConnection.objects.select_related("business").prefetch_related("logs").order_by("business__name", "platform")
    serializer_class = IntegrationConnectionSerializer
    permission_classes = [IsAdminView]
    pagination_class = None
    filterset_fields = ["platform", "business", "status"]

    def perform_create(self, serializer):
        # each new connection gets its own webhook secret
        serializer.save(webhook_secret=secrets.token_hex(16))

    @action(detail=False, methods=["get"])
    def catalogue(self, request):
        """Platform catalogue for the 'Add integration' picker."""
        return Response([
            {"slug": slug, "label": meta["label"], "source": meta["source"],
             "fields": meta.get("fields", []), "poll": bool(meta.get("poll"))}
            for slug, meta in PLATFORMS.items()
        ])

    @action(detail=True, methods=["post"])
    def connect(self, request, pk=None):
        conn = self.get_object()
        conn.status = "connected"
        if not conn.webhook_secret:
            conn.webhook_secret = secrets.token_hex(16)
        if "config" in request.data:
            conn.config = request.data["config"]
        if "auto_assign" in request.data:
            conn.auto_assign = bool(request.data["auto_assign"])
        conn.save()
        return Response(self.get_serializer(conn).data)

    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        conn = self.get_object()
        conn.status = "disconnected"
        conn.save(update_fields=["status"])
        return Response(self.get_serializer(conn).data)

    @action(detail=True, methods=["post"])
    def regenerate_secret(self, request, pk=None):
        conn = self.get_object()
        conn.webhook_secret = secrets.token_hex(16)
        conn.save(update_fields=["webhook_secret"])
        return Response(self.get_serializer(conn).data)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Pull data from a poll connector (FXArtha) into the CRM. Optionally
        accepts {config: {base_url, api_key}} to save before syncing."""
        conn = self.get_object()
        if not PLATFORMS.get(conn.platform, {}).get("poll"):
            return Response({"detail": "This connection is not a poll connector."}, status=400)
        if "config" in request.data:
            conn.config = {**(conn.config or {}), **request.data["config"]}
            conn.save(update_fields=["config"])
        if "auto_assign" in request.data:
            conn.auto_assign = bool(request.data["auto_assign"])
            conn.save(update_fields=["auto_assign"])
        from .services_fxartha import sync_fxartha
        result = sync_fxartha(conn)
        status_code = 400 if result.get("error") else 200
        return Response({**result, **self.get_serializer(conn).data}, status=status_code)

    @action(detail=True, methods=["post"])
    def send_test(self, request, pk=None):
        """Simulate an incoming lead so the pipeline can be tested without the platform."""
        conn = self.get_object()
        sample = {"name": request.data.get("name", "Test Lead"),
                  "email": request.data.get("email", f"test{secrets.randbelow(99999)}@example.com"),
                  "phone": request.data.get("phone", f"+9199{secrets.randbelow(99999999):08d}"),
                  "country": "India", "campaign": "Test Campaign"}
        result = process_webhook(conn, sample)
        return Response({"test": True, **result, **self.get_serializer(conn).data})
