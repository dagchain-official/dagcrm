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
    # DAGChain (Web3 node platform) — poll connector. Auth = sub-admin login
    # (email+password -> token, no OTP), so the sync can refresh its own token.
    "dagchain": {"label": "DAGChain Platform", "source": "DAGChain",
                 "fields": ["base_url", "email", "password"], "poll": True},
}


class IntegrationConnection(models.Model):
    STATUS = [("connected", "Connected"), ("disconnected", "Disconnected")]

    platform = models.CharField(max_length=20)
    # Which business this connection feeds. Null = global (not tied to a business).
    business = models.ForeignKey("crm.Business", on_delete=models.CASCADE,
                                 null=True, blank=True, related_name="integrations")
    name = models.CharField(max_length=120, blank=True)   # custom label, e.g. "FX Artha Instagram"
    status = models.CharField(max_length=20, choices=STATUS, default="disconnected")
    webhook_secret = models.CharField(max_length=64, blank=True)
    config = models.JSONField(default=dict, blank=True)   # tokens / page ids
    auto_assign = models.BooleanField(default=True)        # auto-distribute new leads
    total_leads = models.PositiveIntegerField(default=0)
    last_lead_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # one connection per (platform, business) pair
        unique_together = ("platform", "business")

    def __str__(self):
        return f"{self.label} ({self.status})"

    @property
    def label(self):
        base = PLATFORMS.get(self.platform, {}).get("label", self.platform)
        if self.name:
            return self.name
        if self.business_id:
            return f"{self.business.name} — {base}"
        return base

    @property
    def source_name(self):
        base = PLATFORMS.get(self.platform, {}).get("source", self.platform.title())
        # keep leads traceable to the business (e.g. "Meta Ads · FX Artha")
        if self.business_id:
            return f"{base} · {self.business.name}"
        return base


class DagChainProfile(models.Model):
    """Per-DAGChain-user detail mirrored from /admin/userList."""
    customer = models.OneToOneField("crm.Customer", on_delete=models.CASCADE, related_name="dagchain")
    external_id = models.CharField(max_length=64, unique=True, db_index=True)
    display_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    wallet_address = models.CharField(max_length=90, blank=True)
    user_type = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=30, blank=True)
    email_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(max_length=30, blank=True)
    social_provider = models.CharField(max_length=30, blank=True)
    dgc_balance = models.DecimalField(max_digits=22, decimal_places=6, default=0)
    fuel_wallet_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    referral_code = models.CharField(max_length=40, blank=True)
    referral_count = models.PositiveIntegerField(default=0)          # "followers"
    total_referral_earnings = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    validator_nodes_count = models.PositiveIntegerField(default=0)
    storage_nodes_count = models.PositiveIntegerField(default=0)
    login_count = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-total_referral_earnings", "-dgc_balance"]

    def __str__(self):
        return f"{self.display_name or self.email}"


class DagChainNode(models.Model):
    """A purchased validator / storage node on DAGChain."""
    KIND = [("validator", "Validator"), ("storage", "Storage")]
    customer = models.ForeignKey("crm.Customer", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="dagchain_nodes")
    external_id = models.CharField(max_length=64, unique=True, db_index=True)
    kind = models.CharField(max_length=12, choices=KIND)
    node_key = models.CharField(max_length=80, blank=True)
    package = models.CharField(max_length=80, blank=True)        # packageName / tierName
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=30, blank=True)
    payment_status = models.CharField(max_length=30, blank=True)
    uptime = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    blocks_validated = models.PositiveIntegerField(default=0)
    rewards_earned = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    pending_rewards = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    claimed_rewards = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    effective_apy = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    capacity = models.CharField(max_length=40, blank=True)       # storage only
    is_staked = models.BooleanField(default=False)
    staked_amount = models.DecimalField(max_digits=22, decimal_places=6, default=0)        # DGC staked on the node
    staking_requirement = models.DecimalField(max_digits=22, decimal_places=6, default=0)  # DGC required to stake
    opened_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchase_price"]

    def __str__(self):
        return f"{self.kind} · {self.node_key}"


class DagChainCommissionRate(models.Model):
    """Single global config: what an RM earns on their DAGChain users' activity.

    Three separate bases, because a validator node, a storage node and staked
    DGC are not worth the same to the business. Node rates are a percentage of
    the node's purchase price (money), so they pay out in the node currency.
    The staking rate is a percentage of the DGC staked, so it pays out in DGC —
    the CRM holds no DGC price, so the two are never added together.
    """
    validator_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    storage_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    staking_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    @classmethod
    def get_solo(cls):
        return cls.objects.order_by("id").first() or cls.objects.create()

    def __str__(self):
        return "DAGChain commission rates"


class IntegrationLog(models.Model):
    connection = models.ForeignKey(IntegrationConnection, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=20)   # success / error / skipped
    message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
