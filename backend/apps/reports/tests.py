"""Reports: DAGChain per-RM commission, and the Target Board's target source."""
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


class TargetBoardSourceTests(TestCase):
    """The board shows ONLY targets that were actually assigned. No assignment
    means no target — delete one and it leaves the board entirely, rather than
    silently reverting to a CTC × multiplier figure nobody set."""

    def setUp(self):
        from apps.crm.models import Target, TargetAssignment
        self.Target, self.TargetAssignment = Target, TargetAssignment
        role = Role.objects.create(name="Sales Executive")
        self.rm = User.objects.create_user(email="rm2@dagos.test", name="Rita",
                                           password="x", role=role)
        # salary 10,000 and the default global multiplier of 1 -> derived target
        self.emp = Employee.objects.create(user=self.rm, salary=10000)

    def _board(self):
        from apps.reports.targets import compute_targets

        def walk(nodes):
            for n in nodes:
                yield n
                yield from walk(n["reports"])
        tree = compute_targets(7, 2026)["tree"]
        return next(n for n in walk(tree) if n["user_id"] == self.rm.id)

    def _assign(self, value):
        t = self.Target.objects.create(name="July", target_type="revenue", value=value,
                                       start_date="2026-07-01", end_date="2026-07-31")
        self.TargetAssignment.objects.create(target=t, user=self.rm)
        return t

    def _company(self, month=7):
        from apps.reports.targets import compute_targets
        return compute_targets(month, 2026)["company"]

    def test_no_assignment_means_no_target(self):
        row = self._board()
        self.assertEqual(row["target"], 0)
        self.assertFalse(row["assigned"])
        self.assertEqual(self._company()["target"], 0)
        # the CTC × multiplier figure is still offered, but only as a suggestion
        self.assertEqual(row["suggested"], round(row["ctc"] * row["multiplier"], 2))
        self.assertGreater(row["suggested"], 0)

    def test_an_assigned_target_is_what_the_board_shows(self):
        self._assign(25000)
        row = self._board()
        self.assertEqual(row["target"], 25000.0)
        self.assertTrue(row["assigned"])
        self.assertEqual(self._company()["target"], 25000.0)

    def test_deleting_the_target_clears_it_from_the_board(self):
        t = self._assign(25000)
        self.assertEqual(self._board()["target"], 25000.0)

        t.delete()
        row = self._board()
        self.assertEqual(row["target"], 0)          # gone, not reverted to a formula
        self.assertFalse(row["assigned"])
        self.assertEqual(self._company()["target"], 0)

    def test_incentives_measure_against_the_assigned_target(self):
        from apps.reports.incentives import compute_incentives

        def target_for(month=7):
            rows = compute_incentives(month, 2026)["rows"]
            return next(r for r in rows if r["id"] == self.emp.id)["target"]

        # nothing assigned -> falls back to CTC × multiplier, so a month with no
        # target can't read as 0% attainment and hand out a deduction
        self.assertEqual(target_for(), self._board()["suggested"])

        self._assign(25000)
        self.assertEqual(target_for(), 25000.0)

    def test_the_targets_list_is_scoped_and_names_the_assignee(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import Role as _Role
        outsider = User.objects.create_user(
            email="out@dagos.test", name="Outsider", password="x",
            role=_Role.objects.create(name="Sales Manager"))
        Employee.objects.create(user=outsider, salary=1000)
        theirs = self.Target.objects.create(name="Theirs", target_type="revenue",
                                            value=1, start_date="2026-07-01",
                                            end_date="2026-07-31")
        self.TargetAssignment.objects.create(target=theirs, user=outsider)
        self._assign(25000)

        from apps.accounts.models import ModulePermission
        ModulePermission.objects.create(role=self.rm.role, module="targets", can_view=True)
        c = APIClient()
        c.force_authenticate(user=self.rm)
        rows = c.get("/api/targets/").data["results"]

        self.assertEqual([r["assigned_to"] for r in rows], ["Rita"])   # not Outsider's
        self.assertEqual(rows[0]["value"], "25000.00")

    def test_achieved_counts_only_the_assignees_revenue(self):
        from apps.crm.models import Customer
        from apps.crm.serializers import TargetSerializer
        from apps.sales.models import Revenue

        other = User.objects.create_user(email="other@dagos.test", name="Other",
                                         password="x", role=self.rm.role)
        mine = Customer.objects.create(name="Mine", assigned_to=self.rm)
        yours = Customer.objects.create(name="Yours", assigned_to=other)
        # net_revenue is recomputed on save (gross − commission), so set gross
        Revenue.objects.create(customer=mine, gross_revenue=4000)
        Revenue.objects.create(customer=yours, gross_revenue=6000)

        t = self._assign(25000)
        self.assertEqual(TargetSerializer(t).data["achieved"], 4000.0)

    def test_a_target_for_another_month_does_not_leak(self):
        t = self.Target.objects.create(name="June", target_type="revenue", value=99000,
                                       start_date="2026-06-01", end_date="2026-06-30")
        self.TargetAssignment.objects.create(target=t, user=self.rm)
        self.assertEqual(self._board()["target"], 0)        # July
        self.assertFalse(self._board()["assigned"])
        self.assertEqual(self._company(month=6)["target"], 99000.0)
