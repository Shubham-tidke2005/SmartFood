from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)
from apps.recommendations.models import (
    MatchTrainingRecord,
    RecommendationEvaluation,
    RecommendationRun,
)
from apps.recommendations.training_data import (
    collect_training_records,
)


class TrainingDataCollectionTests(TestCase):
    password = "SmartFoodTest@123"

    def setUp(self):
        now = timezone.now()

        self.donor = User.objects.create_user(
            email="training-donor@example.com",
            password=self.password,
            display_name="Training Donor",
            role=User.Role.DONOR,
            is_active=True,
            contact_verified_at=now,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

        self.receiver = User.objects.create_user(
            email="training-receiver@example.com",
            password=self.password,
            display_name="Training Receiver",
            role=User.Role.RECEIVER,
            is_active=True,
            contact_verified_at=now,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

        self.category = FoodCategory.objects.create(
            code="training-meals",
            name="Training Meals",
            active=True,
            requires_preparation_time=True,
            requires_use_by=True,
        )

        self.donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.COMPLETED,
            closed_at=now,
        )

        self.revision = (
            DonationRevision.objects.create(
                donation=self.donation,
                number=1,
                is_current=True,
                food_name="Training Meal",
                category=self.category,
                quantity=Decimal("20.000"),
                unit=DonationRevision.Unit.PORTION,
                description="Training record",
                storage_condition="Covered",
                pickup_address="Test address",
                pickup_starts_at=(
                    now - timedelta(hours=4)
                ),
                pickup_deadline=(
                    now - timedelta(hours=2)
                ),
                proposed_by=self.donor,
                prepared_at=(
                    now - timedelta(hours=5)
                ),
                use_by_at=(
                    now - timedelta(hours=1)
                ),
                pickup_area="Central Zone",
            )
        )

        self.run = RecommendationRun.objects.create(
            donation=self.donation,
            revision=self.revision,
            requested_by=self.donor,
            algorithm=(
                RecommendationRun.Algorithm
                .RULE_BASED_V2
            ),
            model_version="baseline-2.0",
            status=(
                RecommendationRun.Status.COMPLETED
            ),
            weights={
                "distance": 0.30,
                "quantity_match": 0.30,
                "availability_overlap": 0.20,
                "transport_readiness": 0.20,
            },
            considered_count=1,
            eligible_count=1,
            candidate_count=1,
        )

        RecommendationRun.objects.filter(
            pk=self.run.pk
        ).update(
            created_at=(
                now - timedelta(hours=6)
            )
        )

        self.run.refresh_from_db()

        self.evaluation = (
            RecommendationEvaluation.objects.create(
                run=self.run,
                receiver=self.receiver,
                eligible=True,
                rejection_reasons=[],
                eligibility_checks={
                    "food_compatible": True,
                    "collection_feasible": True,
                },
                feature_snapshot={
                    "category_id": str(
                        self.category.id
                    ),
                    "category_name": (
                        self.category.name
                    ),
                    "unit": (
                        DonationRevision.Unit.PORTION
                    ),
                    "donation_quantity": "20.000",
                    "remaining_capacity": "30.000",
                    "approximate_distance_km": "2.50",
                    "maximum_service_distance_km": "10.00",
                    "active_allocations": 0,
                    "maximum_active_allocations": 3,
                    "normalized_features": {
                        "distance": 0.75,
                        "quantity_match": 0.666667,
                        "availability_overlap": 1.0,
                        "transport_readiness": 1.0,
                    },
                },
                baseline_score=Decimal("83.00"),
            )
        )

        self.approved_at = (
            now - timedelta(hours=5)
        )

        self.donation_request = (
            DonationRequest.objects.create(
                donation=self.donation,
                receiver=self.receiver,
                requested_revision=self.revision,
                status=(
                    DonationRequest.Status.APPROVED
                ),
                proposed_mode=(
                    DonationRequest.TransportMode
                    .RECEIVER_COLLECTION
                ),
                expires_at=(
                    now - timedelta(hours=2)
                ),
                decided_at=self.approved_at,
                reason="",
            )
        )

        self.history = (
            DonationStatusHistory.objects.create(
                donation=self.donation,
                actor=self.receiver,
                event_type=(
                    "RECEIPT_CONFIRMED"
                ),
                from_status=(
                    Donation.Status.DELIVERED
                ),
                to_status=(
                    Donation.Status.COMPLETED
                ),
                reason="",
            )
        )

        DonationStatusHistory.objects.filter(
            pk=self.history.pk
        ).update(
            created_at=now
        )

    def test_completed_approved_match_is_collected(
        self,
    ):
        statistics = collect_training_records(
            dataset_source=(
                MatchTrainingRecord
                .DatasetSource.PILOT
            ),
        )

        self.assertEqual(
            statistics["created"],
            1,
        )

        record = (
            MatchTrainingRecord.objects.get()
        )

        self.assertTrue(
            record.target_completed
        )

        self.assertEqual(
            record.dataset_source,
            MatchTrainingRecord
            .DatasetSource.PILOT,
        )

        self.assertEqual(
            record.baseline_version,
            "baseline-2.0",
        )

        self.assertEqual(
            record.feature_snapshot[
                "normalized_features"
            ]["distance"],
            0.75,
        )

    def test_collection_is_idempotent(
        self,
    ):
        collect_training_records(
            dataset_source=(
                MatchTrainingRecord
                .DatasetSource.PILOT
            ),
        )

        statistics = collect_training_records(
            dataset_source=(
                MatchTrainingRecord
                .DatasetSource.PILOT
            ),
        )

        self.assertEqual(
            MatchTrainingRecord.objects.count(),
            1,
        )

        self.assertEqual(
            statistics["already_exists"],
            1,
        )

    def test_unresolved_match_is_not_collected(
        self,
    ):
        self.donation.status = (
            Donation.Status.DELIVERED
        )

        self.donation.closed_at = None

        self.donation.save(
            update_fields=[
                "status",
                "closed_at",
            ]
        )

        statistics = collect_training_records(
            dataset_source=(
                MatchTrainingRecord
                .DatasetSource.PILOT
            ),
        )

        self.assertEqual(
            statistics["examined"],
            0,
        )

        self.assertEqual(
            MatchTrainingRecord.objects.count(),
            0,
        )

    def test_unselected_receiver_is_not_failure_label(
        self,
    ):
        other_receiver = (
            User.objects.create_user(
                email="unselected@example.com",
                password=self.password,
                display_name=(
                    "Unselected Receiver"
                ),
                role=User.Role.RECEIVER,
                is_active=True,
            )
        )

        RecommendationEvaluation.objects.create(
            run=self.run,
            receiver=other_receiver,
            eligible=True,
            rejection_reasons=[],
            eligibility_checks={},
            feature_snapshot={
                "normalized_features": {
                    "distance": 0.5,
                    "quantity_match": 0.5,
                    "availability_overlap": 0.5,
                    "transport_readiness": 0.5,
                },
            },
            baseline_score=Decimal("50.00"),
        )

        collect_training_records(
            dataset_source=(
                MatchTrainingRecord
                .DatasetSource.PILOT
            ),
        )

        self.assertEqual(
            MatchTrainingRecord.objects.count(),
            1,
        )

        self.assertFalse(
            MatchTrainingRecord.objects.filter(
                recommendation_evaluation__receiver=(
                    other_receiver
                )
            ).exists()
        )