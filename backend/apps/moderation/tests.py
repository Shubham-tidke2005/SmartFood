from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRevision,
    FoodCategory,
)

from .models import VerificationSubmission


class VerificationPermissionTests(APITestCase):
    def setUp(self):
        now = timezone.now()

        self.admin = User.objects.create_user(
            email="admin-test@example.com",
            display_name="Test Administrator",
            role=User.Role.ADMIN,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified_at=now,
            is_staff=True,
            is_superuser=True,
            password="StrongTestPassword@123",
        )

        self.donor = User.objects.create_user(
            email="donor-test@example.com",
            display_name="Test Donor",
            role=User.Role.DONOR,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified_at=now,
            password="StrongTestPassword@123",
        )

        self.receiver = User.objects.create_user(
            email="pending-receiver@example.com",
            display_name="Pending Receiver",
            role=User.Role.RECEIVER,
            verification_status=(
                User.VerificationStatus.PENDING
            ),
            contact_verified_at=now,
            password="StrongTestPassword@123",
        )

        category = FoodCategory.objects.create(
            code="verification-test-food",
            name="Verification Test Food",
        )

        self.donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.AVAILABLE,
        )

        DonationRevision.objects.create(
            donation=self.donation,
            number=1,
            is_current=True,
            food_name="Test Meals",
            category=category,
            quantity="10.000",
            unit=DonationRevision.Unit.PORTION,
            description="Synthetic test food",
            storage_condition="Keep covered",
            pickup_address="Synthetic test address",
            pickup_starts_at=(
                now + timedelta(hours=1)
            ),
            pickup_deadline=(
                now + timedelta(hours=5)
            ),
            proposed_by=self.donor,
        )

        self.submission = (
            VerificationSubmission.objects.create(
                user=self.receiver,
                attempt=1,
                status=(
                    VerificationSubmission.Status.PENDING
                ),
                submitted_details={
                    "legal_name": "Pending Receiver",
                    "address": "Synthetic address",
                    "role": "RECEIVER",
                },
            )
        )

    def test_unapproved_receiver_cannot_request_donation(
        self,
    ):
        self.client.force_authenticate(
            user=self.receiver
        )

        response = self.client.post(
            reverse(
                "donations:request-create",
                kwargs={
                    "donation_id": self.donation.id,
                },
            ),
            {
                "proposed_mode": "RECEIVER_COLLECTION",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_approve_verification(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse(
                "moderation:verification-approve",
                kwargs={
                    "submission_id": self.submission.id,
                },
            ),
            {
                "reason": (
                    "Documents reviewed and accepted."
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.receiver.refresh_from_db()

        self.assertEqual(
            self.receiver.verification_status,
            User.VerificationStatus.VERIFIED,
        )

    def test_approved_receiver_can_request_donation(self):
        self.client.force_authenticate(
            user=self.admin
        )

        approval_response = self.client.post(
            reverse(
                "moderation:verification-approve",
                kwargs={
                    "submission_id": self.submission.id,
                },
            ),
            {
                "reason": (
                    "Documents reviewed and accepted."
                )
            },
            format="json",
        )

        self.assertEqual(
            approval_response.status_code,
            status.HTTP_200_OK,
        )

        self.receiver.refresh_from_db()

        self.client.force_authenticate(
            user=self.receiver
        )

        request_response = self.client.post(
            reverse(
                "donations:request-create",
                kwargs={
                    "donation_id": self.donation.id,
                },
            ),
            {
                "proposed_mode": "RECEIVER_COLLECTION",
            },
            format="json",
        )

        self.assertEqual(
            request_response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_rejection_requires_reason(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            reverse(
                "moderation:verification-reject",
                kwargs={
                    "submission_id": self.submission.id,
                },
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )