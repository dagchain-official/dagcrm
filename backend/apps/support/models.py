from django.conf import settings
from django.db import models


# ------------------------------------------------------------------ Tickets
class Ticket(models.Model):
    PRIORITY = [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")]
    STATUS = [
        ("open", "Open"), ("assigned", "Assigned"), ("in_progress", "In Progress"),
        ("resolved", "Resolved"), ("closed", "Closed"),
    ]
    ticket_no = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey("crm.Customer", on_delete=models.CASCADE, related_name="tickets")
    category = models.CharField(max_length=80, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY, default="medium")
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.ticket_no


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
