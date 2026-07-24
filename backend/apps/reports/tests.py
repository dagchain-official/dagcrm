"""Reports: DAGChain per-RM commission, and the Target Board's target source."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role
from apps.crm.models import Customer
from apps.hr.models import Employee
from apps.integrations.models import CommissionRule, DagChainNode, DagChainProfile
from apps.reports.dagchain_rm import compute_dagchain_by_rm

User = get_user_model()


def _rule(platform, key, rate, employee=None):
    return CommissionRule.objects.create(platform=platform, product_key=key,
                                         rate=rate, employee=employee)


class DagChainCommissionTests(TestCase):
    """Commission is PER PRODUCT (the node's package), universal with a per-RM
    override, plus a staking rate paid in DGC."""

    def setUp(self):
        role = Role.objects.create(name="Sales Executive")
        self.rm = User.objects.create_user(email="rm@dagos.test", name="Rita",
                                           password="x", role=role)
        self.emp = Employee.objects.create(user=self.rm)
        self.cust = Customer.objects.create(name="Punit Saini", external_id="dc-1",
                                            assigned_to=self.rm)
        DagChainProfile.objects.create(customer=self.cust, dgc_balance=2, staked_amount=500)
        # 3 "Pioneer Tier" validators @ 3000, 1 "Starter" storage @ 1019
        for i in range(3):
            DagChainNode.objects.create(customer=self.cust, external_id=f"v{i}",
                                        kind="validator", package="Pioneer Tier",
                                        purchase_price=3000)
        DagChainNode.objects.create(customer=self.cust, external_id="s0", kind="storage",
                                    package="Starter Storage", purchase_price=1019)

        _rule("dagchain", "Pioneer Tier", 5)
        _rule("dagchain", "Starter Storage", 2)
        _rule("dagchain", "staking", 10)

    def _row(self, **kw):
        data = compute_dagchain_by_rm(**kw)
        return data, data["employees"][0]["customers"][0]

    def test_each_product_is_paid_at_its_own_rate(self):
        data, row = self._row()
        self.assertEqual(row["validator_spend"], 9000.0)
        self.assertEqual(row["storage_spend"], 1019.0)
        self.assertEqual(row["comm_validator"], 450.0)      # 9000 * 5%
        self.assertEqual(row["comm_storage"], 20.38)        # 1019 * 2%
        self.assertEqual(row["commission"], 470.38)         # money total
        self.assertEqual(row["comm_staking"], 50.0)         # 500 DGC * 10%, paid in DGC
        # DGC commission must NOT be folded into the money total
        self.assertNotEqual(row["commission"], row["commission"] + row["comm_staking"])

    def test_a_per_rm_override_beats_the_universal_rate(self):
        _rule("dagchain", "Pioneer Tier", 8, employee=self.emp)   # Rita gets 8%
        _, row = self._row()
        self.assertEqual(row["comm_validator"], 720.0)      # 9000 * 8%, not 5%
        self.assertEqual(row["comm_storage"], 20.38)        # storage still universal 2%

    def test_a_product_with_no_rule_pays_nothing(self):
        CommissionRule.objects.filter(product_key="Starter Storage").delete()
        _, row = self._row()
        self.assertEqual(row["comm_storage"], 0)
        self.assertEqual(row["comm_validator"], 450.0)      # the others still pay

    def test_totals_roll_up_to_the_employee_and_the_grand_row(self):
        data, row = self._row()
        emp = data["employees"][0]
        self.assertEqual(emp["commission"], row["commission"])
        self.assertEqual(data["grand"]["commission"], row["commission"])
        self.assertEqual(data["grand"]["comm_staking"], row["comm_staking"])

    def test_an_unassigned_book_earns_no_commission(self):
        self.cust.assigned_to = None
        self.cust.save(update_fields=["assigned_to"])
        _, row = self._row()
        self.assertEqual(row["commission"], 0)
        self.assertEqual(row["comm_staking"], 0)
        self.assertEqual(row["node_spend"], 10019.0)        # revenue still reported


class TradersLotsBookTests(TestCase):
    """Lots & Commission is the RM's BOOK: every trader assigned to them, not
    only the ones who happen to have traded."""

    def setUp(self):
        from apps.crm.models import MetricDefinition, MetricEntry
        self.MetricEntry = MetricEntry
        self.metric = MetricDefinition.objects.create(name="Lots Traded")
        role = Role.objects.create(name="Sales Executive")
        self.rm = User.objects.create_user(email="rm3@dagos.test", name="Himanshu",
                                           password="x", role=role)
        self.emp = Employee.objects.create(user=self.rm, salary=1000)

    def _trader(self, name, lots=None):
        from apps.crm.models import Customer
        c = Customer.objects.create(name=name, external_id=f"fx-{name}",
                                    assigned_to=self.rm)
        if lots is not None:
            self.MetricEntry.objects.create(metric=self.metric, customer=c,
                                            employee=self.emp, value=lots,
                                            date="2026-07-10")
        return c

    def test_traders_with_no_lots_still_count_on_the_book(self):
        from apps.reports.traders import compute_traders_lots
        for i in range(8):
            self._trader(f"traded-{i}", lots=i + 1)
        for i in range(6):
            self._trader(f"never-traded-{i}")          # no lots row at all

        data = compute_traders_lots(7, 2026, rate=2)
        me = next(e for e in data["employees"] if e["employee_id"] == self.emp.id)

        self.assertEqual(me["trader_count"], 14)       # not 8
        self.assertEqual(data["grand"]["traders"], 14)
        self.assertEqual(me["lots_total"], 36.0)       # 1+2+…+8
        self.assertEqual(me["commission_total"], 72.0)

        zero = [t for t in me["traders"] if t["lots_total"] == 0]
        self.assertEqual(len(zero), 6)
        self.assertEqual(zero[0]["commission_total"], 0)

    def test_a_trader_with_no_rm_is_listed_as_unassigned(self):
        from apps.crm.models import Customer
        from apps.reports.traders import compute_traders_lots
        Customer.objects.create(name="Orphan", external_id="fx-orphan")

        names = {e["name"] for e in compute_traders_lots(7, 2026)["employees"]}
        self.assertIn("Unassigned", names)

    def test_per_lot_commission_uses_the_universal_rate_then_the_rm_override(self):
        from apps.reports.traders import compute_traders_lots
        self._trader("A", lots=10)

        # universal $2/lot
        _rule("fxartha", "lots", 2)
        me = compute_traders_lots(7, 2026)["employees"][0]
        self.assertEqual(me["rate"], 2.0)
        self.assertEqual(me["commission_total"], 20.0)

        # Himanshu overridden to $5/lot
        _rule("fxartha", "lots", 5, employee=self.emp)
        me = compute_traders_lots(7, 2026)["employees"][0]
        self.assertEqual(me["rate"], 5.0)
        self.assertEqual(me["commission_total"], 50.0)


class CommissionRulesEndpointTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        admin = User.objects.create_user(email="a@dagos.test", name="Admin",
                                         password="x", is_superuser=True)
        role = Role.objects.create(name="Sales Executive")
        self.rm = User.objects.create_user(email="rm@dagos.test", name="Rita",
                                           password="x", role=role)
        self.emp = Employee.objects.create(user=self.rm)
        Customer.objects.create(name="N", external_id="dc-x", assigned_to=self.rm)
        DagChainNode.objects.create(customer=Customer.objects.first(), external_id="n1",
                                    kind="validator", package="Pioneer Tier", purchase_price=3000)
        self.client_ = APIClient()
        self.client_.force_authenticate(user=admin)

    def test_products_list_includes_the_node_package_and_lots(self):
        res = self.client_.get("/api/reports/commission-rules/")
        self.assertEqual(res.status_code, 200)
        dc_keys = [p["key"] for p in res.data["products"]["dagchain"]]
        self.assertIn("Pioneer Tier", dc_keys)
        self.assertIn("staking", dc_keys)
        self.assertEqual([p["key"] for p in res.data["products"]["fxartha"]],
                         ["lots", "brokerage", "deposit"])
        self.assertEqual([e["id"] for e in res.data["employees"]], [self.emp.id])

    def test_put_sets_universal_and_override_then_delete_clears(self):
        from apps.integrations.models import CommissionRule
        self.client_.put("/api/reports/commission-rules/",
                         {"platform": "dagchain", "product_key": "Pioneer Tier", "rate": 5},
                         format="json")
        self.client_.put("/api/reports/commission-rules/",
                         {"platform": "dagchain", "product_key": "Pioneer Tier",
                          "employee": self.emp.id, "rate": 8}, format="json")
        self.assertEqual(CommissionRule.objects.count(), 2)

        res = self.client_.get("/api/reports/commission-rules/")
        universal = next(p for p in res.data["products"]["dagchain"] if p["key"] == "Pioneer Tier")
        self.assertEqual(universal["rate"], 5.0)
        self.assertEqual(res.data["overrides"]["dagchain"][str(self.emp.id)]["Pioneer Tier"], 8.0)

        # blank rate deletes the rule
        self.client_.put("/api/reports/commission-rules/",
                         {"platform": "dagchain", "product_key": "Pioneer Tier", "rate": ""},
                         format="json")
        self.assertFalse(CommissionRule.objects.filter(product_key="Pioneer Tier",
                                                       employee__isnull=True).exists())

    def test_a_non_admin_cannot_change_rates(self):
        from rest_framework.test import APIClient
        c = APIClient(); c.force_authenticate(user=self.rm)
        res = c.put("/api/reports/commission-rules/",
                    {"platform": "fxartha", "product_key": "lots", "rate": 9}, format="json")
        self.assertEqual(res.status_code, 403)


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
        Employee.objects.create(user=other, salary=1000)
        mine = Customer.objects.create(name="Mine", assigned_to=self.rm)
        yours = Customer.objects.create(name="Yours", assigned_to=other)
        # net_revenue is recomputed on save (gross − commission), so set gross
        Revenue.objects.create(customer=mine, gross_revenue=4000)
        Revenue.objects.create(customer=yours, gross_revenue=6000)

        t = self._assign(25000)
        self.assertEqual(TargetSerializer(t).data["achieved"], 4000.0)

    def test_a_managers_target_counts_their_teams_revenue(self):
        """The Targets list, the Target Board and the incentive run must all
        report the same number for a manager who owns no customers."""
        from apps.crm.models import Customer
        from apps.crm.serializers import TargetSerializer
        from apps.reports.targets import rollup_for_incentives
        from apps.sales.models import Revenue

        mgr = User.objects.create_user(email="tl@dagos.test", name="Team Lead",
                                       password="x", role=self.rm.role)
        mgr_emp = Employee.objects.create(user=mgr, salary=30000)
        self.emp.manager = mgr
        self.emp.save(update_fields=["manager"])
        Revenue.objects.create(
            customer=Customer.objects.create(name="C", assigned_to=self.rm),
            gross_revenue=73932.76)

        t = self.Target.objects.create(name="TL", target_type="revenue", value=60000,
                                       start_date="2026-07-01", end_date="2026-07-31")
        self.TargetAssignment.objects.create(target=t, user=mgr)

        self.assertEqual(TargetSerializer(t).data["achieved"], 73932.76)   # list
        self.assertEqual(self._board()["achieved"], 73932.76)              # board (the RM)
        self.assertEqual(rollup_for_incentives(7, 2026)[mgr_emp.id]["revenue"],
                         73932.76)                                          # incentives

    def test_a_manager_is_graded_on_their_team_not_on_zero(self):
        """A manager owns no customers, so revenue attributed straight to them is
        0. Grading them on that used to read as 0% and dock their pay while the
        team was over target."""
        from apps.crm.models import Customer
        from apps.reports.incentives import compute_incentives
        from apps.reports.targets import rollup_for_incentives
        from apps.sales.models import Revenue

        mgr = User.objects.create_user(email="mgr3@dagos.test", name="Kamni",
                                       password="x", role=self.rm.role)
        mgr_emp = Employee.objects.create(user=mgr, salary=20000)
        self.emp.manager = mgr                     # the RM now reports to them
        self.emp.save(update_fields=["manager"])

        cust = Customer.objects.create(name="C", assigned_to=self.rm)
        Revenue.objects.create(customer=cust, gross_revenue=50000)
        self._assign(20000)                        # the RM's target: comfortably beaten

        roll = rollup_for_incentives(7, 2026)
        self.assertEqual(roll[self.emp.id]["revenue"], 50000.0)
        # the manager inherits the team's target and revenue
        self.assertEqual(roll[mgr_emp.id]["target"], 20000.0)
        self.assertEqual(roll[mgr_emp.id]["revenue"], 50000.0)
        self.assertTrue(roll[mgr_emp.id]["is_manager"])

        rows = {r["id"]: r for r in compute_incentives(7, 2026)["rows"]}
        self.assertEqual(rows[mgr_emp.id]["attainment"], 250.0)
        self.assertEqual(rows[mgr_emp.id]["deduction"], 0)      # no longer docked
        self.assertGreaterEqual(rows[mgr_emp.id]["total"], 0)

    def test_a_manager_keeps_their_own_sales_on_top_of_the_team(self):
        from apps.crm.models import Customer
        from apps.reports.targets import rollup_for_incentives
        from apps.sales.models import Revenue

        mgr = User.objects.create_user(email="mgr4@dagos.test", name="Selling Mgr",
                                       password="x", role=self.rm.role)
        mgr_emp = Employee.objects.create(user=mgr, salary=20000)
        self.emp.manager = mgr
        self.emp.save(update_fields=["manager"])

        Revenue.objects.create(customer=Customer.objects.create(name="Team", assigned_to=self.rm),
                               gross_revenue=1000)
        Revenue.objects.create(customer=Customer.objects.create(name="Own", assigned_to=mgr),
                               gross_revenue=400)

        self.assertEqual(rollup_for_incentives(7, 2026)[mgr_emp.id]["revenue"], 1400.0)

    def test_a_target_for_another_month_does_not_leak(self):
        t = self.Target.objects.create(name="June", target_type="revenue", value=99000,
                                       start_date="2026-06-01", end_date="2026-06-30")
        self.TargetAssignment.objects.create(target=t, user=self.rm)
        self.assertEqual(self._board()["target"], 0)        # July
        self.assertFalse(self._board()["assigned"])
        self.assertEqual(self._company(month=6)["target"], 99000.0)
