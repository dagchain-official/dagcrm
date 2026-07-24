"""DAGChain contract-level staking: sync aggregation onto profiles + snapshot."""
from django.test import TestCase

from apps.crm.models import Customer
from apps.integrations.models import DagChainProfile
from apps.integrations.services_dagchain import _sync_products, _sync_staking


class _FakeClient:
    """Stands in for the DAGChain _Client — serves canned staking responses."""

    def __init__(self, info, stakes):
        self._info, self._stakes = info, stakes

    def get(self, path, params=None):
        if path == "/admin/staking-contract/info":
            return {"result": self._info}
        return {}

    def paginate(self, path, limit=100):
        yield from self._stakes


class _ProductClient:
    """Serves canned product-catalogue responses keyed by path."""

    def __init__(self, by_path):
        self._by_path = by_path

    def get(self, path, params=None):
        return {"result": self._by_path.get(path, {})}


class ProductCatalogTests(TestCase):
    def test_tiers_packages_and_apr_are_normalised(self):
        client = _ProductClient({
            "/admin/validator-tiers": {"tiers": [
                {"name": "Elite Tier", "packageId": "validator_elite_tier", "price": 5999,
                 "totalKeys": 3000, "soldKeys": 4, "availableNodes": 2996,
                 "status": "active", "isActive": True},
                {"name": "Old Tier", "price": 1, "isActive": False},   # dropped
            ]},
            "/admin/storage-packages": {"packages": [
                {"name": "Starter Storage Node", "pricePerByte": 1.862645149230957e-08,
                 "minCapacityBytes": 1073741824, "maxCapacityBytes": 1073741824000,
                 "allowedUnits": ["GB"], "status": "active"},
                {"name": "Dead", "pricePerByte": 0, "status": "inactive"},   # dropped
            ]},
            "/rewards/apr-rates": {
                "validator": {"basic": {"effectiveApr": 15, "minLockPeriod": 180}},
                "storage": {"starter": {"effectiveApr": 12, "minLockPeriod": 90}},
            },
        })
        snap = _sync_products(client)

        self.assertEqual([v["name"] for v in snap["validators"]], ["Elite Tier"])
        v = snap["validators"][0]
        self.assertEqual((v["price"], v["sold"], v["available"]), (5999.0, 4, 2996))

        self.assertEqual([s["name"] for s in snap["storage"]], ["Starter Storage Node"])
        s = snap["storage"][0]
        self.assertEqual(s["price_per_gb"], 20.0)          # pricePerByte * 1 GiB
        self.assertEqual(s["min_gb"], 1.0)
        self.assertEqual(s["max_gb"], 1000.0)

        self.assertEqual(snap["apr_rates"], [
            {"kind": "Validator", "tier": "Basic", "apr": 15.0, "min_lock_days": 180},
            {"kind": "Storage", "tier": "Starter", "apr": 12.0, "min_lock_days": 90},
        ])

    def test_a_missing_catalogue_endpoint_is_tolerated(self):
        snap = _sync_products(_ProductClient({}))     # every path returns {}
        self.assertEqual(snap, {"validators": [], "storage": [], "apr_rates": []})


def _profile(uid, name):
    c = Customer.objects.create(name=name, external_id=uid)
    return DagChainProfile.objects.create(customer=c, external_id=uid, staked_amount=99)


class StakingSyncTests(TestCase):
    INFO = {
        "contractAddress": "0xabc", "explorerUrl": "https://ex", "owner": "0xowner",
        "chainId": 707070, "totalDgccStaked": 4, "rewardPoolBalance": 500,
        "tranches": [
            {"trancheId": 0, "label": "Stage 1", "durationDays": 365,
             "dgccApyPercent": 12, "isActive": True},
            {"trancheId": 1, "label": "Stage 2", "durationDays": 730,
             "dgccApyPercent": 18, "isActive": False},
        ],
    }

    def test_stakes_aggregate_onto_the_right_profiles(self):
        a = _profile("u-a", "Alice")
        b = _profile("u-b", "Bob")
        _profile("u-c", "Carol")            # no stake this round
        stakes = [
            {"userId": {"_id": "u-a"}, "stakedAmount": 1, "status": "active"},
            {"userId": {"_id": "u-a"}, "stakedAmount": 10, "status": "locked"},
            {"userId": "u-b", "stakedAmount": 5, "status": "active"},   # id as a bare string
            {"userId": {"_id": "u-x"}, "stakedAmount": 7, "status": "active"},  # unknown user
        ]
        snap = _sync_staking(_FakeClient(self.INFO, stakes))

        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(float(a.staked_amount), 11.0)
        self.assertEqual(a.staked_stakes, 2)
        self.assertEqual(float(b.staked_amount), 5.0)
        self.assertEqual(b.staked_stakes, 1)

        # totalDgccStaked from the contract wins; registrations = active+locked rows
        self.assertEqual(snap["total_staked"], 4)
        self.assertEqual(snap["reward_pool"], 500)
        self.assertEqual(snap["registrations"], 4)
        self.assertEqual(snap["stakers"], 3)                 # a, b, x
        self.assertEqual(snap["owner"], "0xowner")
        self.assertEqual([t["apy"] for t in snap["tranches"]], [12, 18])
        self.assertEqual([t["active"] for t in snap["tranches"]], [True, False])

    def test_a_withdrawn_stake_resets_the_profile_to_zero(self):
        a = _profile("u-a", "Alice")
        _sync_staking(_FakeClient(self.INFO,
                                  [{"userId": {"_id": "u-a"}, "stakedAmount": 3, "status": "active"}]))
        a.refresh_from_db()
        self.assertEqual(float(a.staked_amount), 3.0)

        # next sync: this user no longer appears -> back to 0, not left stale
        _sync_staking(_FakeClient(self.INFO, []))
        a.refresh_from_db()
        self.assertEqual(float(a.staked_amount), 0.0)
        self.assertEqual(a.staked_stakes, 0)
