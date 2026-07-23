"""Who may assign targets is a PERMISSION, and its reach is always downwards."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.access import can_assign_targets, can_assign_to
from apps.accounts.models import ModulePermission, Role
from apps.hr.models import Employee

User = get_user_model()


class AssignTargetsPermissionTests(TestCase):
    def setUp(self):
        # head -> manager -> rm   (the org chain the reach is measured along)
        self.head = self._person("Business Head", "head@dagos.test", None)
        self.mgr = self._person("Sales Manager", "mgr@dagos.test", self.head)
        self.rm = self._person("Sales Executive", "rm@dagos.test", self.mgr)
        # a second manager on the same rung, with their own report
        self.other_mgr = self._person("Sales Manager", "mgr2@dagos.test", self.head,
                                      role_obj=self.mgr.role)
        self.other_rm = self._person("Sales Executive", "rm2@dagos.test", self.other_mgr,
                                     role_obj=self.rm.role)

    def _person(self, role_name, email, manager, role_obj=None):
        role = role_obj or Role.objects.create(name=role_name)
        u = User.objects.create_user(email=email, name=email.split("@")[0],
                                     password="x", role=role)
        Employee.objects.create(user=u, manager=manager, salary=1000)
        return u

    def _grant(self, role, allowed):
        ModulePermission.objects.update_or_create(
            role=role, module="assign-targets",
            defaults={"can_view": allowed, "can_create": allowed,
                      "can_edit": False, "can_delete": False})

    # ---- the permission itself ------------------------------------------
    def test_the_matrix_decides_not_the_role_name(self):
        self._grant(self.mgr.role, True)
        self.assertTrue(can_assign_targets(self.mgr))

        self._grant(self.mgr.role, False)
        self.assertFalse(can_assign_targets(self.mgr))

    def test_a_role_with_no_matrix_row_falls_back_to_the_default_set(self):
        ModulePermission.objects.filter(module="assign-targets").delete()
        self.assertTrue(can_assign_targets(self.head))     # Business Head: default on
        self.assertFalse(can_assign_targets(self.rm))      # Sales Executive: default off

    def test_granting_it_to_a_team_leader_works(self):
        tl = self._person("Team Leader", "tl@dagos.test", self.mgr)
        self._grant(tl.role, True)
        self.assertTrue(can_assign_targets(tl))

    # ---- reach: own subtree, downwards only ------------------------------
    def test_an_assigner_reaches_their_own_subtree(self):
        self._grant(self.mgr.role, True)
        self.assertTrue(can_assign_to(self.mgr, self.rm.id))

    def test_an_assigner_cannot_reach_a_peer_or_their_manager(self):
        self._grant(self.mgr.role, True)
        self.assertFalse(can_assign_to(self.mgr, self.other_mgr.id))   # peer
        self.assertFalse(can_assign_to(self.mgr, self.head.id))        # above
        self.assertFalse(can_assign_to(self.mgr, self.other_rm.id))    # another team

    def test_self_is_only_reachable_for_a_team_or_business_rollup(self):
        self._grant(self.mgr.role, True)
        self.assertFalse(can_assign_to(self.mgr, self.mgr.id))
        self.assertTrue(can_assign_to(self.mgr, self.mgr.id, allow_self=True))

    def test_someone_without_the_permission_reaches_nobody(self):
        self._grant(self.rm.role, False)
        self.assertFalse(can_assign_to(self.rm, self.rm.id, allow_self=True))

    def test_a_head_reaches_the_whole_chain_below_them(self):
        self._grant(self.head.role, True)
        for target in (self.mgr, self.rm, self.other_mgr, self.other_rm):
            self.assertTrue(can_assign_to(self.head, target.id), target.email)

    def test_the_super_admin_reaches_everyone(self):
        boss = User.objects.create_user(email="root@dagos.test", name="Root",
                                        password="x", is_superuser=True)
        self.assertTrue(can_assign_targets(boss))
        self.assertTrue(can_assign_to(boss, self.other_rm.id))    # outside any subtree


class AssignTargetPickerTests(AssignTargetsPermissionTests):
    """The Assign Target pickers must offer exactly what the API will accept —
    and must work for a Team Leader, who holds the assign permission but has
    neither the `users` nor the `teams` module."""

    def _client(self, user):
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_a_team_leader_gets_a_populated_people_list(self):
        tl = self._person("Team Leader", "tl@dagos.test", self.mgr)
        rm = self._person("Sales Executive", "tlrm@dagos.test", tl, role_obj=self.rm.role)
        self._grant(tl.role, True)

        res = self._client(tl).get("/api/users/subordinates/")
        self.assertEqual(res.status_code, 200)          # not 403 — no `users` module needed
        self.assertEqual([r["id"] for r in res.data], [rm.id])

    def test_the_people_list_stops_at_the_edge_of_the_subtree(self):
        self._grant(self.mgr.role, True)
        ids = [r["id"] for r in self._client(self.mgr).get("/api/users/subordinates/").data]
        self.assertIn(self.rm.id, ids)
        for outsider in (self.head, self.other_mgr, self.other_rm, self.mgr):
            self.assertNotIn(outsider.id, ids)

    def test_business_scope_includes_the_caller_but_individual_does_not(self):
        self._grant(self.mgr.role, True)
        c = self._client(self.mgr)
        self.assertNotIn(self.mgr.id,
                         [r["id"] for r in c.get("/api/users/subordinates/?scope=user").data])
        self.assertIn(self.mgr.id,
                      [r["id"] for r in c.get("/api/users/subordinates/?scope=business").data])

    def test_someone_without_the_permission_gets_an_empty_list(self):
        self._grant(self.rm.role, False)
        self.assertEqual(self._client(self.rm).get("/api/users/subordinates/").data, [])

    def test_only_teams_fully_inside_the_subtree_are_offered(self):
        from apps.accounts.models import Team, TeamMember
        self._grant(self.mgr.role, True)

        mine = Team.objects.create(name="Mine", leader=self.mgr)
        TeamMember.objects.create(team=mine, user=self.rm)
        theirs = Team.objects.create(name="Theirs", leader=self.other_mgr)
        TeamMember.objects.create(team=theirs, user=self.other_rm)
        mixed = Team.objects.create(name="Mixed", leader=self.mgr)
        TeamMember.objects.create(team=mixed, user=self.other_rm)   # one outsider
        Team.objects.create(name="Empty")

        names = [t["name"] for t in self._client(self.mgr).get("/api/teams/assignable/").data]
        self.assertEqual(names, ["Mine"])
        for excluded in ("Theirs", "Mixed", "Empty"):
            self.assertNotIn(excluded, names)
