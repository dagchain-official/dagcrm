"""A call/meeting activity's outcome drives the lead's status."""
from django.test import TestCase

from apps.crm.models import Lead, LeadActivity, LeadSource


class OutcomeAdvanceTests(TestCase):
    def _lead(self, status="new"):
        return Lead.objects.create(lead_code=f"L{status}{Lead.objects.count()}",
                                   name="Test", status=status)

    def _log(self, lead, **kw):
        # the post_save signal advances the status
        LeadActivity.objects.create(lead=lead, activity_type=kw.pop("activity_type", "call"), **kw)
        lead.refresh_from_db()
        return lead.status

    def test_call_outcomes_move_the_lead(self):
        cases = {
            "no_answer": "attempted", "connected": "contacted",
            "interested": "qualified", "meeting_booked": "meeting_booked",
        }
        for outcome, expected in cases.items():
            with self.subTest(outcome=outcome):
                self.assertEqual(self._log(self._lead(), outcome=outcome), expected)

    def test_not_interested_parks_in_nurture_and_wrong_number_loses(self):
        self.assertEqual(self._log(self._lead("qualified"), outcome="not_interested"), "nurture")
        self.assertEqual(self._log(self._lead("contacted"), outcome="wrong_number"), "lost")

    def test_converted_closes_won(self):
        self.assertEqual(self._log(self._lead("qualified"), outcome="converted"), "converted")

    def test_meeting_status_moves_the_lead(self):
        self.assertEqual(self._log(self._lead("contacted"), activity_type="meeting",
                                   meeting_status="confirmed"), "meeting_booked")
        self.assertEqual(self._log(self._lead("meeting_booked"), activity_type="meeting",
                                   meeting_status="completed"), "meeting_done")

    def test_status_never_moves_backward_or_revives_a_closed_lead(self):
        # a plain call on a qualified lead must not drag it back to contacted
        self.assertEqual(self._log(self._lead("qualified"), outcome="connected"), "qualified")
        # a closed-won lead stays won
        self.assertEqual(self._log(self._lead("converted"), outcome="interested"), "converted")

    def test_duration_and_notes_are_stored(self):
        lead = self._lead()
        a = LeadActivity.objects.create(lead=lead, activity_type="call", outcome="connected",
                                        duration_min=7.5, remarks="Discussed pricing")
        self.assertEqual(float(a.duration_min), 7.5)
        self.assertEqual(a.remarks, "Discussed pricing")
