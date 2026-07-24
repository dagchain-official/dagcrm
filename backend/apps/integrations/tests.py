"""DAGChain contract-level staking: sync aggregation onto profiles + snapshot."""
from django.test import TestCase

from apps.crm.models import Customer
from apps.integrations.models import DagChainProfile
from apps.integrations.services_dagchain import _sync_staking


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
