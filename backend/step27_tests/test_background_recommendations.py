from decimal import Decimal
from unittest.mock import patch
from django.test import override_settings

from apps.donations.models import DonationStatusHistory
from apps.notifications.models import Notification
from apps.operations.models import BackgroundJob
from apps.operations.services import run_background_cycle
from apps.recommendations.inference import ModelInferenceError
from apps.recommendations.services import generate_recommendations
from apps.receivers.models import ReceiverPreference
from .factories import SmartFoodAPICase, api_for


class BackgroundRecommendationTests(SmartFoodAPICase):
    def test_complete_background_cycle_is_idempotent(self):
        donation, _ = self.make_donation(expired=True)
        first = run_background_cycle()
        snapshots = (set(DonationStatusHistory.objects.values_list("id", flat=True)),
                     set(Notification.objects.values_list("id", flat=True)),
                     set(BackgroundJob.objects.values_list("id", flat=True)))
        second = run_background_cycle()
        self.assertEqual(first["donations_expired"], 1)
        self.assertEqual(second["donations_expired"], 0)
        self.assertEqual(snapshots, (set(DonationStatusHistory.objects.values_list("id", flat=True)),
                                    set(Notification.objects.values_list("id", flat=True)),
                                    set(BackgroundJob.objects.values_list("id", flat=True))))
        self.assertEqual(DonationStatusHistory.objects.filter(donation=donation, event_type="EXPIRED").count(), 1)

    @override_settings(SMARTFOOD_RECOMMENDATIONS={"BASELINE_VERSION": "baseline-2.0", "BASELINE_WEIGHTS": {
        "distance": 0.3, "quantity_match": 0.3, "availability_overlap": 0.2, "transport_readiness": 0.2}})
    def test_inference_failure_returns_baseline_and_preserves_normal_operations(self):
        donation, _ = self.make_donation()
        ReceiverPreference.objects.filter(receiver=self.other_receiver).update(active=False)
        with patch("apps.recommendations.services.score_candidates_with_model", side_effect=ModelInferenceError("synthetic failure")) as inference:
            with self.assertLogs("apps.recommendations.services", level="ERROR"):
                run = generate_recommendations(donation=donation, requested_by=self.donor)
        inference.assert_called_once()
        self.assertEqual(run.algorithm, "RULE_BASED_V2")
        self.assertEqual(run.model_version, "baseline-2.0")
        self.assertIn("synthetic failure", run.error_message)
        self.assertEqual((run.considered_count, run.eligible_count, run.candidate_count), (2, 1, 1))
        candidate = run.candidates.get()
        self.assertEqual(candidate.receiver_id, self.receiver.pk)
        self.assertEqual(candidate.score, Decimal(candidate.feature_snapshot["baseline_score"]))
        self.assertTrue(candidate.explanations)
        evaluation = run.evaluations.get(receiver=self.other_receiver)
        self.assertFalse(evaluation.eligible)
        self.assertTrue(evaluation.rejection_reasons)
        response = self.post_as(self.receiver, "donations:request-create", {"donation_id": donation.pk},
                                {"proposed_mode": "RECEIVER_COLLECTION"})
        self.assert_status(response, 201)
        self.assert_status(self.post_as(self.donor, "donations:request-approve", {"request_id": response.data["id"]}), 200)

    def test_unexpected_model_error_also_falls_back(self):
        donation, _ = self.make_donation()
        with patch("apps.recommendations.services.score_candidates_with_model", side_effect=RuntimeError("synthetic failure")):
            with self.assertLogs("apps.recommendations.services", level="ERROR"):
                run = generate_recommendations(donation=donation, requested_by=self.donor)
        self.assertEqual(run.algorithm, "RULE_BASED_V2")
        self.assertEqual(run.candidate_count, 2)
        self.assertIn("RuntimeError", run.error_message)
        self.assert_status(api_for(self.receiver).get("/api/donations/"), 200)
