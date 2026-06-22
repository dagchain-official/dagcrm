from rest_framework import serializers

from .models import Ticket, TicketComment


class TicketCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = TicketComment
        fields = ["id", "ticket", "user", "user_name", "comment", "created_at"]
        read_only_fields = ["created_at"]


class TicketSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    assigned_name = serializers.CharField(source="assigned_to.name", read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "ticket_no", "customer", "customer_name", "category", "priority",
                  "status", "assigned_to", "assigned_name", "comments", "created_at"]
        read_only_fields = ["created_at"]
