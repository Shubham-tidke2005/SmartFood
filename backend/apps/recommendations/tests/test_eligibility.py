from datetime import time, timedelta
from decimal import Decimal

from django.test import TestCase
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
from apps.recommendations.eligibility import (
    evaluate_receiver_eligibility,
    find_pickup_service_area,
    get_eligible_candidates,
)


class EligibilityFilteringTests(TestCase):
    password = "SmartFoodTest@123"

    def setUp(self):
        now = timezone.now()

        self.donor = User.objects.create_user(
            email="eligibility-donor@example.com",
            password=self.password,
            display_name="Eligibility Donor",
            role=User.Role.DONOR,
            is_active=True,
            contact_verified_at=now,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

        self.receiver = User.objects.create_user(
            email="eligible-receiver@example.com",
            password=self.password,
            display_name="Eligible Receiver",
            role=User.Role.RECEIVER,
            is_active=True,
            contact_verified_at=now,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

        self.pickup_area = (
            ServiceArea.objects.create(
                code="central-zone",
                name="Central Zone",
                latitude=Decimal("19.997500"),
                longitude=Decimal("73.789800"),
                active=True,
            )
        )

        self.receiver_area = (
            ServiceArea.objects.create(
                code="receiver-zone",
                name="Receiver Zone",
                latitude=Decimal("20.002000"),
                longitude=Decimal("73.794000"),
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

        self.profile = (
            ReceiverProfile.objects.create(
                user=self.receiver,
                organization_name=(
                    "Eligible Receiver Organization"
                ),
                address="Receiver address",
                service_area=self.receiver_area,
                max_service_distance_km=(
                    Decimal("20.00")
                ),
                max_active_allocations=3,
                operational=True,
            )
        )

        ReceiverPreference.objects.create(
            receiver=self.receiver,
            category=self.category,
            active=True,
        )

        self.requirement = (
            ReceiverRequirement.objects.create(
                receiver=self.receiver,
                category=self.category,
                unit=DonationRevision.Unit.PORTION,
                quantity_needed=Decimal("100.000"),
                quantity_reserved=Decimal("0.000"),
                needed_until=(
                    timezone.localdate()
                    + timedelta(days=7)
                ),
                active=True,
            )
        )

        self.donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.AVAILABLE,
        )

        pickup_start = (
            timezone.now()
            + timedelta(hours=2)
        )

        pickup_deadline = (
            pickup_start
            + timedelta(hours=4)
        )

        self.revision = (
            DonationRevision.objects.create(
                donation=self.donation,
                number=1,
                is_current=True,
                food_name="Vegetable Rice Meals",
                category=self.category,
                quantity=Decimal("25.000"),
                unit=(
                    DonationRevision.Unit.PORTION
                ),
                description=(
                    "Freshly prepared rice meals."
                ),
                storage_condition=(
                    "Keep covered"
                ),
                pickup_address=(
                    "Central Zone pickup address"
                ),
                pickup_starts_at=pickup_start,
                pickup_deadline=(
                    pickup_deadline
                ),
                proposed_by=self.donor,
                prepared_at=timezone.now(),
                use_by_at=pickup_deadline,
                pickup_area=(
                    self.pickup_area.name
                ),
            )
        )

        local_pickup_start = (
            timezone.localtime(
                pickup_start
            )
        )

        ReceiverAvailability.objects.create(
            receiver=self.receiver,
            weekday=(
                local_pickup_start.weekday()
            ),
            starts_at=time(0, 1),
            ends_at=time(23, 59),
            active=True,
        )

    def get_decision(self):
        pickup_service_area = (
            find_pickup_service_area(
                self.revision.pickup_area
            )
        )

        return evaluate_receiver_eligibility(
            profile=self.profile,
            donation=self.donation,
            revision=self.revision,
            pickup_service_area=(
                pickup_service_area
            ),
        )

    def test_verified_compatible_receiver_is_eligible(
        self,
    ):
        decision = self.get_decision()

        self.assertTrue(
            decision.eligible,
            decision.rejection_reasons,
        )

        self.assertEqual(
            decision.requirement,
            self.requirement,
        )

        self.assertIsNotNone(
            decision.approximate_distance_km
        )

        self.assertTrue(
            decision.checks[
                "collection_feasible"
            ]
        )

    def test_eligible_candidate_list_contains_receiver(
        self,
    ):
        candidates = get_eligible_candidates(
            donation=self.donation,
            revision=self.revision,
        )

        self.assertEqual(
            len(candidates),
            1,
        )

        self.assertEqual(
            candidates[0].profile.user,
            self.receiver,
        )

    def test_unverified_receiver_is_rejected(
        self,
    ):
        self.receiver.verification_status = (
            User.VerificationStatus.PENDING
        )
        self.receiver.save(
            update_fields=[
                "verification_status"
            ]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)

        self.assertFalse(
            decision.checks[
                "participant_verified"
            ]
        )

    def test_inactive_receiver_is_rejected(
        self,
    ):
        self.receiver.is_active = False
        self.receiver.save(
            update_fields=["is_active"]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "account_active"
            ]
        )

    def test_non_operational_profile_is_rejected(
        self,
    ):
        self.profile.operational = False
        self.profile.save(
            update_fields=["operational"]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "profile_operational"
            ]
        )

    def test_food_incompatibility_rejects_receiver(
        self,
    ):
        ReceiverPreference.objects.filter(
            receiver=self.receiver,
            category=self.category,
        ).update(active=False)

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "food_compatible"
            ]
        )

    def test_insufficient_capacity_rejects_receiver(
        self,
    ):
        self.requirement.quantity_needed = (
            Decimal("10.000")
        )
        self.requirement.save(
            update_fields=["quantity_needed"]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "capacity_available"
            ]
        )

    def test_receiver_without_availability_is_rejected(
        self,
    ):
        ReceiverAvailability.objects.filter(
            receiver=self.receiver
        ).update(active=False)

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "receiving_available"
            ]
        )

    def test_receiver_outside_service_distance_is_rejected(
        self,
    ):
        self.profile.max_service_distance_km = (
            Decimal("0.10")
        )
        self.profile.save(
            update_fields=[
                "max_service_distance_km"
            ]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "within_service_distance"
            ]
        )

    def test_unknown_pickup_area_is_rejected(
        self,
    ):
        self.revision.pickup_area = (
            "Unconfigured Area"
        )
        self.revision.save(
            update_fields=["pickup_area"]
        )

        decision = self.get_decision()

        self.assertFalse(decision.eligible)
        self.assertFalse(
            decision.checks[
                "service_area_resolved"
            ]
        )