from django.db import models

# Platform catalogue: slug -> (label, lead source name, config fields client must give)
PLATFORMS = {
    "meta": {"label": "Meta Lead Ads", "source": "Meta Ads",
             "fields": ["page_id", "access_token"]},
    "google": {"label": "Google Ads", "source": "Google Ads",
               "fields": []},
    "whatsapp": {"label": "WhatsApp Business", "source": "WhatsApp",
                 "fields": ["phone_number_id", "access_token"]},
    "linkedin": {"label": "LinkedIn Lead Gen", "source": "LinkedIn",
                 "fields": ["access_token"]},
    "tiktok": {"label": "TikTok Lead Gen", "source": "TikTok",
               "fields": ["access_token"]},
    "website": {"label": "Website / Landing Page", "source": "Website",
                "fields": []},
    "telegram": {"label": "Telegram Bot", "source": "Telegram",
                 "fields": ["bot_token"]},
    # Poll connector (not a webhook): pulls leads/customers/revenue/AUM from an
    # external trading platform's read-only CRM API. Config = base_url + api_key.
    "fxartha": {"label": "FXArtha Platform", "source": "FXArtha",
                "fields": ["base_url", "api_key"], "poll": True},
}


class IntegrationConnection(models.Model):
    STATUS = [("connected", "Connected"), ("disconnected", "Disconnected")]

    platform = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS, default="disconnected")
    webhook_secret = models.CharField(max_length=64, blank=True)
    config = models.JSONField(default=dict, blank=True)   # tokens / page ids
    auto_assign = models.BooleanField(default=True)        # auto-distribute new leads
    total_leads = models.PositiveIntegerField(default=0)
    last_lead_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} ({self.status})"

    @property
    def label(self):
        return PLATFORMS.get(self.platform, {}).get("label", self.platform)

    @property
    def source_name(self):
        return PLATFORMS.get(self.platform, {}).get("source", self.platform.title())


class IntegrationLog(models.Model):
    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=20)   # success / error / skipped
    message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
