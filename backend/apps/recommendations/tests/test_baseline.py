from datetime import datetime, time, timedelta
from decimal import Decimal

from django.test import (
    TestCase,
    override_settings,
)

from django.utils import timezone

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRevision,
    FoodCategory,
)
from apps.receivers.models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)
from apps.recommendations.models import (
    RecommendationCandidate,
    RecommendationEvaluation,
    RecommendationRun,
)
from apps.recommendations.services import (
    generate_recommendations,
)

@override_settings(
    SMARTFOOD_ML={
        "ENABLED": False,
    }
)

class RuleBasedBaselineTests(TestCase):
    password = "SmartFoodTest@123"

    def setUp(self):
        now = timezone.now()

        self.donor = User.objects.create_user(
            email="baseline-donor@example.com",
            password=self.password,
            display_name="Baseline Donor",
            role=User.Role.DONOR,
            is_active=True,
            contact_verified_at=now,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

        self.eligible_receiver = (
            User.objects.create_user(
                email="eligible@example.com",
                password=self.password,
                display_name=(
                    "Eligible Receiver"
                ),
                role=User.Role.RECEIVER,
                is_active=True,
                contact_verified_at=now,
                verification_status=(
                    User.VerificationStatus
                    .VERIFIED
                ),
            )
        )

        self.ineligible_receiver = (
            User.objects.create_user(
                email="ineligible@example.com",
                password=self.password,
                display_name=(
                    "Ineligible Receiver"
                ),
                role=User.Role.RECEIVER,
                is_active=True,
                contact_verified_at=now,
                verification_status=(
                    User.VerificationStatus
                    .VERIFIED
                ),
            )
        )

        self.service_area = (
            ServiceArea.objects.create(
                code="central-zone",
                name="Central Zone",
                latitude=Decimal("19.997500"),
                longitude=Decimal("73.789800"),
                active=True,
            )
        )

        self.category = (
            FoodCategory.objects.create(
                code="prepared-meals",
                name="Prepared Meals",
                active=True,
                requires_preparation_time=True,
                requires_use_by=True,
            )
        )

        self.eligible_profile = (
            ReceiverProfile.objects.create(
                user=self.eligible_receiver,
                organization_name=(
                    "Eligible Organization"
                ),
                address=(
                    "Central Zone address"
                ),
                service_area=(
                    self.service_area
                ),
                max_service_distance_km=(
                    Decimal("10.00")
                ),
                max_active_allocations=3,
                operational=True,
            )
        )

        self.ineligible_profile = (
            ReceiverProfile.objects.create(
                user=self.ineligible_receiver,
                organization_name=(
                    "Ineligible Organization"
                ),
                address=(
                    "Central Zone address"
                ),
                service_area=(
                    self.service_area
                ),
                max_service_distance_km=(
                    Decimal("10.00")
                ),
                max_active_allocations=3,
                operational=True,
            )
        )

        ReceiverPreference.objects.create(
            receiver=self.eligible_receiver,
            category=self.category,
            active=True,
        )

        ReceiverRequirement.objects.create(
            receiver=self.eligible_receiver,
            category=self.category,
            unit=DonationRevision.Unit.PORTION,
            quantity_needed=Decimal("25.000"),
            quantity_reserved=Decimal("0.000"),
            needed_until=(
                timezone.localdate()
                + timedelta(days=5)
            ),
            active=True,
        )

        self.donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.AVAILABLE,
        )

        local_timezone = (
            timezone.get_current_timezone()
        )

        pickup_date = (
            timezone.localdate()
            + timedelta(days=1)
        )

        pickup_starts_at = (
            timezone.make_aware(
                datetime.combine(
                    pickup_date,
                    time(10, 0),
                ),
                local_timezone,
            )
        )

        pickup_deadline = (
            timezone.make_aware(
                datetime.combine(
                    pickup_date,
                    time(14, 0),
                ),
                local_timezone,
            )
        )

        self.revision = (
            DonationRevision.objects.create(
                donation=self.donation,
                number=1,
                is_current=True,
                food_name=(
                    "Vegetable Rice Meals"
                ),
                category=self.category,
                quantity=Decimal("25.000"),
                unit=(
                    DonationRevision.Unit.PORTION
                ),
                description=(
                    "Freshly prepared meals."
                ),
                storage_condition=(
                    "Keep covered"
                ),
                pickup_address=(
                    "Central Zone pickup"
                ),
                pickup_starts_at=(
                    pickup_starts_at
                ),
                pickup_deadline=(
                    pickup_deadline
                ),
                proposed_by=self.donor,
                prepared_at=timezone.now(),
                use_by_at=pickup_deadline,
                pickup_area=(
                    self.service_area.name
                ),
            )
        )

        ReceiverAvailability.objects.create(
            receiver=self.eligible_receiver,
            weekday=pickup_date.weekday(),
            starts_at=time(9, 0),
            ends_at=time(17, 0),
            active=True,
        )

    def test_baseline_saves_run_and_ranked_candidate(
        self,
    ):
        run = generate_recommendations(
            donation=self.donation,
            requested_by=self.donor,
        )

        self.assertEqual(
            run.algorithm,
            RecommendationRun.Algorithm
            .RULE_BASED_V2,
        )

        self.assertEqual(
            run.model_version,
            "baseline-2.0",
        )

        self.assertEqual(
            run.considered_count,
            2,
        )

        self.assertEqual(
            run.eligible_count,
            1,
        )

        self.assertEqual(
            run.candidate_count,
            1,
        )

        candidate = (
            RecommendationCandidate.objects.get(
                run=run
            )
        )

        self.assertEqual(
            candidate.receiver,
            self.eligible_receiver,
        )

        self.assertEqual(
            candidate.rank,
            1,
        )

        self.assertEqual(
            candidate.score,
            Decimal("100.00"),
        )

    def test_all_considered_receivers_are_recorded(
        self,
    ):
        run = generate_recommendations(
            donation=self.donation,
            requested_by=self.donor,
        )

        evaluations = (
            RecommendationEvaluation.objects
            .filter(run=run)
        )

        self.assertEqual(
            evaluations.count(),
            2,
        )

        eligible_evaluation = (
            evaluations.get(
                receiver=(
                    self.eligible_receiver
                )
            )
        )

        rejected_evaluation = (
            evaluations.get(
                receiver=(
                    self.ineligible_receiver
                )
            )
        )

        self.assertTrue(
            eligible_evaluation.eligible
        )

        self.assertEqual(
            eligible_evaluation
            .baseline_score,
            Decimal("100.00"),
        )

        self.assertFalse(
            rejected_evaluation.eligible
        )

        self.assertIsNone(
            rejected_evaluation
            .baseline_score
        )

        self.assertGreater(
            len(
                rejected_evaluation
                .rejection_reasons
            ),
            0,
        )

    def test_feature_values_are_saved(
        self,
    ):
        run = generate_recommendations(
            donation=self.donation,
            requested_by=self.donor,
        )

        candidate = (
            RecommendationCandidate.objects.get(
                run=run
            )
        )

        snapshot = (
            candidate.feature_snapshot
        )

        self.assertIn(
            "normalized_features",
            snapshot,
        )

        normalized = snapshot[
            "normalized_features"
        ]

        self.assertEqual(
            normalized["distance"],
            1.0,
        )

        self.assertEqual(
            normalized["quantity_match"],
            1.0,
        )

        self.assertEqual(
            normalized[
                "availability_overlap"
            ],
            1.0,
        )

        self.assertEqual(
            normalized[
                "transport_readiness"
            ],
            1.0,
        )

    def test_weights_are_saved_with_run(
        self,
    ):
        run = generate_recommendations(
            donation=self.donation,
            requested_by=self.donor,
        )

        self.assertEqual(
            run.weights,
            {
                "distance": 0.3,
                "quantity_match": 0.3,
                "availability_overlap": 0.2,
                "transport_readiness": 0.2,
            },
        )

    def test_non_available_donation_is_rejected(
        self,
    ):
        self.donation.status = (
            Donation.Status.RESERVED
        )

        self.donation.save(
            update_fields=["status"]
        )

        with self.assertRaisesMessage(
            ValueError,
            "Recommendations can only be generated",
        ):
            generate_recommendations(
                donation=self.donation,
                requested_by=self.donor,
            )