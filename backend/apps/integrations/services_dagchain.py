"""DAGChain poll connector — pulls the platform's admin API into the CRM.

  /admin/dashboard        -> snapshot stored on the connection
  /admin/userList         -> upsert Customer   (keyed by external_id = user _id)
  /admin/validator-nodes  -> Revenue (node purchase price)
  /admin/storage-nodes    -> Revenue (node purchase price)

Auth: sub-admin login (email + password) returns a JWT with NO OTP, so the sync
refreshes its own token. The token goes in a `token:` header (NOT Authorization).
Writes are idempotent (update_or_create on external_id) so re-syncing never
duplicates. DAGChain users carry no RM upstream, so everything is attributed to
a demo RM; reassign a customer later from Customer 360 -> "Reassign RM".
"""
import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime

DEFAULT_BASE = "https://api.dagchain.network/api/v1"
DEMO_RM_EMAIL = "dagchain.demo@dagos.com"
DEMO_RM_NAME = "DAGChain Demo RM"


class _Client:
    """Logs in on demand and re-logs in once if the token has expired."""

    def __init__(self, base, email, password):
        self.base = base.rstrip("/")
        self.email = email
        self.password = password
        self.token = None

    def login(self):
        r = requests.post(f"{self.base}/admin/login",
                          json={"email": self.email, "password": self.password}, timeout=30)
        if r.status_code == 401:
            raise RuntimeError("DAGChain login failed — check email/password.")
        r.raise_for_status()
        tok = (r.json().get("result") or {}).get("token")
        if not tok:
            raise RuntimeError("DAGChain login returned no token (OTP may be enabled).")
        self.token = tok

    def get(self, path, params=None, _retry=True):
        if not self.token:
            self.login()
        r = requests.get(f"{self.base}{path}", params=params,
                         headers={"token": self.token}, timeout=45)
        if r.status_code == 401 and _retry:      # token expired -> refresh once
            self.login()
            return self.get(path, params, _retry=False)
        if r.status_code == 401:
            raise RuntimeError("DAGChain: unauthorized (sub-admin lacks permission?).")
        r.raise_for_status()
        return r.json()

    def paginate(self, path, limit=100):
        page = 1
        while True:
            res = self.get(path, {"page": page, "limit": limit}).get("result") or {}
            for d in res.get("docs", []):
                yield d
            if not res.get("hasNextPage"):
                break
            page += 1


def _demo_rm():
    """The placeholder RM every DAGChain customer is attributed to initially."""
    from django.contrib.auth import get_user_model
    from apps.hr.models import Employee
    User = get_user_model()
    user = User.objects.filter(email=DEMO_RM_EMAIL).first()
    if not user:
        user = User.objects.create_user(email=DEMO_RM_EMAIL, name=DEMO_RM_NAME,
                                        password="changeme123")
    emp, _ = Employee.objects.get_or_create(user=user, defaults={"salary": 0})
    return user, emp


def _dt(iso):
    return parse_datetime(iso) if iso else None


def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _sync_user(item, rm_user):
    """One DAGChain user -> CRM Customer + DagChainProfile (full detail)."""
    from apps.crm.models import Customer
    from .models import DagChainProfile
    uid = item.get("_id")
    if not uid:
        return None
    # Many DAGChain users are wallet-connect only (no display name or email), so
    # fall back to a shortened wallet address rather than a blank/"Unknown" row.
    wallet = item.get("walletAddress") or ""
    short_wallet = f"{wallet[:6]}…{wallet[-4:]}" if len(wallet) > 12 else wallet
    name = (item.get("displayName") or item.get("email")
            or short_wallet or f"User {str(uid)[-6:]}")
    cust, _ = Customer.objects.update_or_create(
        external_id=uid,
        defaults={
            "name": name,
            "email": item.get("email") or "",
            "phone": item.get("phoneCountryCode") or "",
        },
    )
    # seed the owner once; never clobber a manual reassignment
    if cust.assigned_to_id is None:
        cust.assigned_to = rm_user
        cust.save(update_fields=["assigned_to"])

    DagChainProfile.objects.update_or_create(
        external_id=uid,
        defaults={
            "customer": cust,
            "display_name": item.get("displayName") or "",
            "email": item.get("email") or "",
            "wallet_address": item.get("walletAddress") or "",
            "user_type": item.get("userType") or "",
            "status": item.get("status") or "",
            "email_verified": bool(item.get("emailVerified")),
            "kyc_status": item.get("kycStatus") or "",
            "social_provider": item.get("socialProvider") or "",
            "dgc_balance": _num(item.get("dgcBalance")),
            "fuel_wallet_usd": _num(item.get("fuelWalletUsd")),
            "referral_code": item.get("referralCode") or "",
            "referral_count": int(_num(item.get("referralCount"))),
            "total_referral_earnings": _num(item.get("totalReferralEarnings")),
            "validator_nodes_count": int(_num(item.get("validatorNodesCount"))),
            "storage_nodes_count": int(_num(item.get("storageNodesCount"))),
            "login_count": int(_num(item.get("loginCount"))),
            "joined_at": _dt(item.get("createdAt")),
        },
    )
    return cust


def _sync_node(node, business, kind):
    """A purchased validator/storage node -> DagChainNode + Revenue row."""
    from apps.crm.models import Customer
    from apps.sales.models import Revenue
    from .models import DagChainNode
    nid = node.get("_id")
    if not nid:
        return False
    price = _num(node.get("purchasePrice") or node.get("pricePaid"))
    owner = node.get("userId") or {}
    cust = Customer.objects.filter(external_id=owner.get("_id")).first() if owner.get("_id") else None

    DagChainNode.objects.update_or_create(
        external_id=nid,
        defaults={
            "customer": cust, "kind": kind,
            "node_key": node.get("nodeKey") or "",
            "package": node.get("packageName") or node.get("tierName") or "",
            "purchase_price": price,
            "currency": node.get("purchaseCurrency") or "",
            "status": node.get("status") or "",
            "payment_status": node.get("paymentStatus") or "",
            "uptime": _num(node.get("uptime")),
            "blocks_validated": int(_num(node.get("blocksValidated"))),
            "rewards_earned": _num(node.get("rewardsEarned")),
            "pending_rewards": _num(node.get("pendingRewards")),
            "claimed_rewards": _num(node.get("claimedRewards")),
            "effective_apy": _num(node.get("effectiveApy") or node.get("annualROI")),
            "capacity": node.get("capacityDisplay") or node.get("storageCapacity") or "",
            "is_staked": bool(node.get("isStaked")),
            "staked_amount": _num(node.get("stakedAmount")),
            "staking_requirement": _num(node.get("stakingRequirement")),
            "opened_at": _dt(node.get("createdAt")),
        },
    )
    if cust and price:
        Revenue.objects.update_or_create(
            external_id=f"dag-{kind[:3]}:{nid}",
            defaults={"customer": cust, "business": business,
                      "gross_revenue": price, "commission": 0},
        )
        return True
    return False


def sync_dagchain(conn):
    from apps.crm.models import Business
    from .models import IntegrationLog

    cfg = conn.config or {}
    base = cfg.get("base_url") or DEFAULT_BASE
    email, password = cfg.get("email"), cfg.get("password")
    if not (email and password):
        msg = "DAGChain needs a sub-admin email + password in the connection config."
        IntegrationLog.objects.create(connection=conn, status="error", message=msg)
        return {"error": msg}

    client = _Client(base, email, password)
    try:
        dashboard = client.get("/admin/dashboard").get("result", {})
        node_stats = client.get("/admin/node-stats").get("result", {})
        business, _ = Business.objects.get_or_create(name="DAGChain")
        rm_user, _ = _demo_rm()

        users = 0
        for item in client.paginate("/admin/userList"):
            if _sync_user(item, rm_user):
                users += 1

        revenue_rows = 0
        for node in client.paginate("/admin/validator-nodes"):
            revenue_rows += int(_sync_node(node, business, "validator"))
        for node in client.paginate("/admin/storage-nodes"):
            revenue_rows += int(_sync_node(node, business, "storage"))
    except (RuntimeError, requests.RequestException) as e:
        IntegrationLog.objects.create(connection=conn, status="error", message=str(e)[:300])
        return {"error": str(e)}

    conn.status = "connected"
    conn.config = {**cfg, "dashboard": dashboard, "node_stats": node_stats,
                   "last_sync": timezone.now().isoformat()}
    conn.total_leads = users
    conn.last_lead_at = timezone.now()
    conn.save()

    summary = {"users_synced": users, "revenue_rows": revenue_rows,
               "dashboard": dashboard, "node_stats": node_stats}
    IntegrationLog.objects.create(
        connection=conn, status="success",
        message=f"{users} users, {revenue_rows} node-revenue rows")
    return summary
