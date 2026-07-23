"""DAGChain per-RM commission — three bases, three rates, two currencies."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role
from apps.crm.models import Customer
from apps.hr.models import Employee
from apps.integrations.models import DagChainCommissionRate, DagChainNode, DagChainProfile
from apps.reports.dagchain_rm import compute_dagchain_by_rm

User = get_user_model()


class DagChainCommissionTests(TestCase):
    def setUp(self):
        role = Role.objects.create(name="Sales Executive")
        self.rm = User.objects.create_user(email="rm@dagos.test", name="Rita",
                                           password="x", role=role)
        self.emp = Employee.objects.create(user=self.rm)
        self.cust = Customer.objects.create(name="Punit Saini", external_id="dc-1",
                                            assigned_to=self.rm)
        DagChainProfile.objects.create(customer=self.cust, dgc_balance=2)
        # 3 validator nodes @ 3000, 1 storage @ 1019, 500 DGC staked in total
        for i in range(3):
            DagChainNode.objects.create(customer=self.cust, external_id=f"v{i}",
                                        kind="validator", purchase_price=3000,
                                        staked_amount=100)
        DagChainNode.objects.create(customer=self.cust, external_id="s0", kind="storage",
                                    purchase_price=1019, staked_amount=200)

        rates = DagChainCommissionRate.get_solo()
        rates.validator_pct, rates.storage_pct, rates.staking_pct = 5, 2, 10
        rates.save()

    def _row(self, **kw):
        data = compute_dagchain_by_rm(**kw)
        return data, data["employees"][0]["customers"][0]

    def test_each_base_is_paid_at_its_own_rate(self):
        data, row = self._row()

        self.assertEqual(row["validator_spend"], 9000.0)
        self.assertEqual(row["storage_spend"], 1019.0)
        self.assertEqual(row["node_spend"], 10019.0)

        self.assertEqual(row["comm_validator"], 450.0)      # 9000 * 5%
        self.assertEqual(row["comm_storage"], 20.38)        # 1019 * 2%
        self.assertEqual(row["commission"], 470.38)         # money total
        self.assertEqual(row["comm_staking"], 50.0)         # 500 DGC * 10%, paid in DGC

        # staking commission is DGC and must NOT be folded into the money total
        self.assertNotEqual(row["commission"], row["commission"] + row["comm_staking"])
        self.assertEqual(data["rates"],
                         {"validator_pct": 5.0, "storage_pct": 2.0, "staking_pct": 10.0})

    def test_totals_roll_up_to_the_employee_and_the_grand_row(self):
        data, row = self._row()
        emp = data["employees"][0]
        self.assertEqual(emp["commission"], row["commission"])
        self.assertEqual(emp["comm_staking"], row["comm_staking"])
        self.assertEqual(data["grand"]["commission"], row["commission"])
        self.assertEqual(data["grand"]["comm_staking"], row["comm_staking"])

    def test_a_preview_override_does_not_touch_the_saved_rates(self):
        _, row = self._row(rate_override={"validator_pct": "10"})
        self.assertEqual(row["comm_validator"], 900.0)      # previewed at 10%
        self.assertEqual(row["comm_storage"], 20.38)        # saved rate still used
        self.assertEqual(float(DagChainCommissionRate.get_solo().validator_pct), 5.0)

    def test_blank_and_junk_overrides_fall_back_to_the_saved_rate(self):
        for bad in ("", None, "abc"):
            with self.subTest(value=bad):
                _, row = self._row(rate_override={"validator_pct": bad})
                self.assertEqual(row["comm_validator"], 450.0)

    def test_zero_rates_mean_zero_commission(self):
        rates = DagChainCommissionRate.get_solo()
        rates.validator_pct = rates.storage_pct = rates.staking_pct = 0
        rates.save()
        _, row = self._row()
        self.assertEqual(row["commission"], 0)
        self.assertEqual(row["comm_staking"], 0)
        self.assertEqual(row["node_spend"], 10019.0)        # revenue still reported
