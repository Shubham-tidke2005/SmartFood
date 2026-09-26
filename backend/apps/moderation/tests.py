from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.donations.models import (
    Donation,
    DonationRequest,
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


User = get_user_model()


class VerificationPermissionTests(APITestCase):
    def setUp(self):
        self.password = "TestPassword@123"

        self.donor = self.create_user(
            email="donor@moderation-test.local",
            display_name="Test Donor",
            role=User.Role.DONOR,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified=True,
        )

        self.pending_receiver = self.create_user(
            email="pending-receiver@moderation-test.local",
            display_name="Pending Receiver",
            role=User.Role.RECEIVER,
            verification_status=(
                User.VerificationStatus.PENDING
            ),
            contact_verified=True,
        )

        self.approved_receiver = self.create_user(
            email="approved-receiver@moderation-test.local",
            display_name="Approved Receiver",
            role=User.Role.RECEIVER,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified=True,
        )

        self.category = FoodCategory.objects.create(
            code="prepared-meals-test",
            name="Prepared Meals Test",
            active=True,
            requires_preparation_time=True,
            requires_use_by=True,
        )

        self.service_area = ServiceArea.objects.create(
            code="COLLEGE_ROAD_TEST",
            name="College Road Test Area",
            latitude=Decimal("19.997500"),
            longitude=Decimal("73.789800"),
            active=True,
        )

        self.approved_receiver_profile = (
            ReceiverProfile.objects.create(
                user=self.approved_receiver,
                organization_name=(
                    "Approved Receiver Organization"
                ),
                address=(
                    "College Road, Nashik, Maharashtra"
                ),
                service_area=self.service_area,
                max_service_distance_km=Decimal("25.00"),
                max_active_allocations=3,
                operational=True,
            )
        )

        ReceiverPreference.objects.create(
            receiver=self.approved_receiver,
            category=self.category,
            active=True,
        )

        ReceiverRequirement.objects.create(
            receiver=self.approved_receiver,
            category=self.category,
            unit=DonationRevision.Unit.PORTION,
            quantity_needed=Decimal("100.000"),
            quantity_reserved=Decimal("0.000"),
            needed_until=(
                timezone.now() + timedelta(days=2)
            ),
            active=True,
        )

        ReceiverAvailability.objects.create(
            receiver=self.approved_receiver,
            weekday=timezone.localdate().weekday(),
            starts_at=time(hour=0, minute=0),
            ends_at=time(hour=23, minute=59),
            active=True,
        )

        self.donation = self.create_available_donation()

    def create_user(
        self,
        *,
        email,
        display_name,
        role,
        verification_status,
        contact_verified,
    ):
        return User.objects.create_user(
            email=email,
            password=self.password,
            display_name=display_name,
            role=role,
            verification_status=verification_status,
            contact_verified_at=(
                timezone.now()
                if contact_verified
                else None
            ),
            is_active=True,
        )

    def create_available_donation(self):
        now = timezone.now()

        donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.AVAILABLE,
            published_at=now,
        )

        DonationRevision.objects.create(
            donation=donation,
            number=1,
            is_current=True,
            food_name="Vegetable Rice Meals",
            category=self.category,
            quantity=Decimal("25.000"),
            unit=DonationRevision.Unit.PORTION,
            description=(
                "Freshly prepared vegetable rice meals."
            ),
            prepared_at=now - timedelta(hours=1),
            use_by_at=now + timedelta(hours=6),
            storage_condition=(
                "Keep covered and collect quickly."
            ),
            pickup_starts_at=(
                now + timedelta(minutes=30)
            ),
            pickup_deadline=now + timedelta(hours=4),
            pickup_address=(
                "College Road, Nashik, Maharashtra"
            ),
            pickup_area="College Road Test Area",
            proposed_by=self.donor,
        )

        return donation

    def request_payload(self):
        return {
            "proposed_mode": (
                DonationRequest.TransportMode
                .RECEIVER_COLLECTION
            ),
        }

    def test_unapproved_receiver_cannot_request_donation(
        self,
    ):
        self.client.force_authenticate(
            user=self.pending_receiver
        )

        response = self.client.post(
            (
                f"/api/donations/"
                f"{self.donation.id}/requests/"
            ),
            self.request_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

        self.assertFalse(
            DonationRequest.objects.filter(
                donation=self.donation,
                receiver=self.pending_receiver,
            ).exists()
        )

    def test_approved_receiver_can_request_donation(
        self,
    ):
        self.client.force_authenticate(
            user=self.approved_receiver
        )

        response = self.client.post(
            (
                f"/api/donations/"
                f"{self.donation.id}/requests/"
            ),
            self.request_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        donation_request = DonationRequest.objects.get(
            donation=self.donation,
            receiver=self.approved_receiver,
        )

        self.assertEqual(
            donation_request.status,
            DonationRequest.Status.PENDING,
        )

        self.assertEqual(
            donation_request.proposed_mode,
            (
                DonationRequest.TransportMode
                .RECEIVER_COLLECTION
            ),
        )

        self.assertEqual(
            donation_request.requested_revision,
            self.donation.revisions.get(
                is_current=True
            ),
        )