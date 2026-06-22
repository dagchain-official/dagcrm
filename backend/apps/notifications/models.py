from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPES = [("info", "Info"), ("success", "Success"), ("warning", "Warning"), ("error", "Error")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=300, blank=True)
    kind = models.CharField(max_length=20, choices=TYPES, default="info")
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


def notify(user, title, body="", kind="info", link=""):
    """Create an in-app notification + optional email (no-op if user missing)."""
    if not user:
        return None
    n = Notification.objects.create(user=user, title=title, body=body, kind=kind, link=link)
    from django.conf import settings
    if getattr(settings, "NOTIFY_EMAIL", False) and getattr(user, "email", ""):
        try:
            from django.core.mail import send_mail
            send_mail(f"[DAGOS] {title}", body or title,
                      settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        except Exception:
            pass
    return n
