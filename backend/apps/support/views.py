from rest_framework import viewsets

from .models import Ticket, TicketComment
from .serializers import TicketCommentSerializer, TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("customer", "assigned_to").prefetch_related("comments").all()
    serializer_class = TicketSerializer
    filterset_fields = ["status", "priority", "assigned_to", "customer"]
    search_fields = ["ticket_no", "category", "customer__name"]

    def perform_update(self, serializer):
        serializer.save()
        # Auto activity tracking: updating a ticket bumps the counter.
        user = self.request.user
        if user and user.is_authenticated:
            from apps.hr.services import bump_activity
            bump_activity(user, "tickets_updated")


class TicketCommentViewSet(viewsets.ModelViewSet):
    queryset = TicketComment.objects.select_related("ticket", "user").all()
    serializer_class = TicketCommentSerializer
    filterset_fields = ["ticket", "user"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
