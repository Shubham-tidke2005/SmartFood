from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)
from apps.notifications.models import Notification
from apps.operations.models import (
    BackgroundJob,
    OperationalIssue,
)
from apps.operations.services import (
    enqueue_notification,
    expire_available_donations,
    expire_unanswered_requests,
    process_notification_jobs,
)


User = get_user_model()


class BackgroundWorkTests(APITestCase):
    def setUp(self):
        self.donor = self.create_user(
            email="background-donor@test.local",
            role=User.Role.DONOR,
        )

        self.receiver = self.create_user(
            email="background-receiver@test.local",
            role=User.Role.RECEIVER,
        )

        self.category = FoodCategory.objects.create(
            code="background-prepared-food",
            name="Background Prepared Food",
            active=True,
            requires_preparation_time=True,
            requires_use_by=True,
        )

    def create_user(self, *, email, role):
        return User.objects.create_user(
            email=email,
            password="TestPassword@123",
            display_name=email.split("@")[0],
            role=role,
            is_active=True,
            contact_verified_at=timezone.now(),
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
        )

    def create_donation(
        self,
        *,
        status=Donation.Status.AVAILABLE,
        deadline=None,
    ):
        current_time = timezone.now()

        deadline = deadline or (
            current_time + timedelta(hours=2)
        )

        donation = Donation.objects.create(
            donor=self.donor,
            status=status,
        )

        revision = DonationRevision.objects.create(
            donation=donation,
            number=1,
            is_current=True,
            food_name="Test Rice Meals",
            category=self.category,
            quantity="20.000",
            unit=DonationRevision.Unit.PORTION,
            description="Test food donation.",
            storage_condition="Keep covered.",
            pickup_address="Test Address",
            pickup_area="Test Area",
            pickup_starts_at=(
                deadline - timedelta(hours=1)
            ),
            pickup_deadline=deadline,
            proposed_by=self.donor,
            prepared_at=(
                current_time - timedelta(hours=1)
            ),
            use_by_at=(
                current_time + timedelta(hours=5)
            ),
        )

        return donation, revision

    def test_expired_donation_is_updated(self):
        current_time = timezone.now()

        donation, _ = self.create_donation(
            deadline=current_time
            - timedelta(minutes=1)
        )

        processed = expire_available_donations(
            current_time=current_time
        )

        donation.refresh_from_db()

        self.assertEqual(processed, 1)

        self.assertEqual(
            donation.status,
            Donation.Status.EXPIRED,
        )

        self.assertIsNotNone(donation.closed_at)

        self.assertEqual(
            DonationStatusHistory.objects.filter(
                donation=donation,
                event_type="EXPIRED",
            ).count(),
            1,
        )

    def test_expiry_job_is_idempotent(self):
        current_time = timezone.now()

        donation, _ = self.create_donation(
            deadline=current_time
            - timedelta(minutes=1)
        )

        first_result = expire_available_donations(
            current_time=current_time
        )

        second_result = expire_available_donations(
            current_time=current_time
        )

        self.assertEqual(first_result, 1)
        self.assertEqual(second_result, 0)

        self.assertEqual(
            DonationStatusHistory.objects.filter(
                donation=donation,
                event_type="EXPIRED",
            ).count(),
            1,
        )

    def test_unanswered_request_expires(self):
        current_time = timezone.now()

        donation, revision = self.create_donation()

        donation_request = DonationRequest.objects.create(
            donation=donation,
            receiver=self.receiver,
            requested_revision=revision,
            status=DonationRequest.Status.PENDING,
            proposed_mode=(
                DonationRequest.TransportMode
                .RECEIVER_COLLECTION
            ),
            expires_at=(
                current_time
                - timedelta(minutes=1)
            ),
        )

        processed = expire_unanswered_requests(
            current_time=current_time
        )

        donation_request.refresh_from_db()

        self.assertEqual(processed, 1)

        self.assertEqual(
            donation_request.status,
            DonationRequest.Status.EXPIRED,
        )

    def test_notification_job_is_idempotent(self):
        key = "test-notification-idempotency"

        enqueue_notification(
            deduplication_key=key,
            recipient_id=self.receiver.id,
            notification_type=(
                Notification.Type.RECEIPT_REMINDER
            ),
            title="Test reminder",
            message="Please confirm receipt.",
            data={"test": True},
        )

        enqueue_notification(
            deduplication_key=key,
            recipient_id=self.receiver.id,
            notification_type=(
                Notification.Type.RECEIPT_REMINDER
            ),
            title="Test reminder",
            message="Please confirm receipt.",
            data={"test": True},
        )

        self.assertEqual(
            BackgroundJob.objects.filter(
                deduplication_key=key
            ).count(),
            1,
        )

        process_notification_jobs()

        process_notification_jobs()

        self.assertEqual(
            Notification.objects.filter(
                deduplication_key=key
            ).count(),
            1,
        )

    def test_background_issue_key_is_unique(self):
        donation, _ = self.create_donation()

        OperationalIssue.objects.create(
            deduplication_key=(
                f"test-issue:{donation.id}"
            ),
            issue_type=(
                OperationalIssue.IssueType
                .MISSED_PICKUP
            ),
            donation=donation,
            summary="Test issue",
        )

        self.assertEqual(
            OperationalIssue.objects.count(),
            1,
        )