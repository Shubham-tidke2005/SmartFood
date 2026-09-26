import base64

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.donations.models import (
    Donation,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)


User = get_user_model()


class DonationAPITests(APITestCase):
    def setUp(self):
        self.donor = self.create_user(
            email="donor@test.local",
            role=User.Role.DONOR,
        )

        self.second_donor = self.create_user(
            email="second-donor@test.local",
            role=User.Role.DONOR,
        )

        self.receiver = self.create_user(
            email="receiver@test.local",
            role=User.Role.RECEIVER,
        )

        self.unverified_receiver = self.create_user(
            email="unverified-receiver@test.local",
            role=User.Role.RECEIVER,
            verified=False,
        )

        self.volunteer = self.create_user(
            email="volunteer@test.local",
            role=User.Role.VOLUNTEER,
        )

        self.category = FoodCategory.objects.create(
            name="Prepared Meals",
            code="prepared-meals",
            active=True,
            requires_preparation_time=True,
            requires_use_by=True,
        )

        self.inactive_category = FoodCategory.objects.create(
            name="Inactive Category",
            code="inactive-category",
            active=False,
            requires_preparation_time=False,
            requires_use_by=False,
        )

    def create_user(
        self,
        *,
        email,
        role,
        verified=True,
    ):
        return User.objects.create_user(
            email=email,
            password="TestPassword@123",
            role=role,
            is_active=True,
            contact_verified_at=(
                timezone.now() if verified else None
            ),
            verification_status=(
                User.VerificationStatus.VERIFIED
                if verified
                else User.VerificationStatus.PENDING
            ),
        )

    def valid_payload(self, **overrides):
        now = timezone.now()

        payload = {
            "food_name": "Vegetable Rice",
            "category_id": str(self.category.id),
            "quantity": "25.000",
            "unit": DonationRevision.Unit.PORTION,
            "description": (
                "Freshly prepared vegetable rice."
            ),
            "storage_condition": (
                "Keep covered and collect quickly."
            ),
            "prepared_at": (
                now - timedelta(hours=1)
            ).isoformat(),
            "use_by_at": (
                now + timedelta(hours=6)
            ).isoformat(),
            "pickup_starts_at": (
                now + timedelta(minutes=30)
            ).isoformat(),
            "pickup_deadline": (
                now + timedelta(hours=4)
            ).isoformat(),
            "pickup_address": (
                "College Road, Nashik, Maharashtra"
            ),
            "pickup_area": "College Road",
        }

        payload.update(overrides)

        return payload

    def create_donation_using_api(self, **overrides):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(**overrides),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        return Donation.objects.get(
            id=response.data["id"]
        )

    def create_valid_png(self):
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
            "CAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )

        return SimpleUploadedFile(
            name="test.png",
            content=png_bytes,
            content_type="image/png",
        )

    def test_verified_donor_can_create_donation(self):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        donation = Donation.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(donation.donor, self.donor)

        self.assertEqual(
            donation.status,
            Donation.Status.AVAILABLE,
        )

        current_revision = donation.revisions.get(
            is_current=True
        )

        self.assertEqual(
            current_revision.food_name,
            "Vegetable Rice",
        )

        self.assertEqual(
            current_revision.quantity,
            Decimal("25.000"),
        )

        self.assertEqual(current_revision.number, 1)

        self.assertEqual(
            current_revision.proposed_by,
            self.donor,
        )

    def test_receiver_cannot_create_donation(self):
        self.client.force_authenticate(self.receiver)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

        self.assertEqual(Donation.objects.count(), 0)

    def test_volunteer_cannot_create_donation(self):
        self.client.force_authenticate(self.volunteer)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

        self.assertEqual(Donation.objects.count(), 0)

    def test_quantity_must_be_positive(self):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(quantity="0.000"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn("quantity", response.data)

    def test_negative_quantity_is_rejected(self):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(quantity="-5.000"),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn("quantity", response.data)

    def test_pickup_deadline_must_be_after_pickup_start(
        self,
    ):
        now = timezone.now()

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(
                pickup_starts_at=(
                    now + timedelta(hours=4)
                ).isoformat(),
                pickup_deadline=(
                    now + timedelta(hours=2)
                ).isoformat(),
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

    def test_pickup_deadline_must_be_in_future(self):
        now = timezone.now()

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(
                pickup_starts_at=(
                    now - timedelta(hours=3)
                ).isoformat(),
                pickup_deadline=(
                    now - timedelta(hours=1)
                ).isoformat(),
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

    def test_prepared_food_requires_preparation_time(
        self,
    ):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(prepared_at=None),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn("prepared_at", response.data)

    def test_category_requiring_use_by_rejects_missing_use_by(
        self,
    ):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(use_by_at=None),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn("use_by_at", response.data)

    def test_use_by_cannot_be_before_preparation_time(
        self,
    ):
        now = timezone.now()

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(
                prepared_at=now.isoformat(),
                use_by_at=(
                    now - timedelta(hours=1)
                ).isoformat(),
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

    def test_inactive_category_cannot_be_used(self):
        self.client.force_authenticate(self.donor)

        response = self.client.post(
            "/api/donations/",
            self.valid_payload(
                category_id=str(
                    self.inactive_category.id
                )
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

    def test_donation_list_can_be_filtered_by_category(
        self,
    ):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(self.receiver)

        response = self.client.get(
            "/api/donations/",
            {
                "category": str(self.category.id),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        results = response.data.get(
            "results",
            response.data,
        )

        donation_ids = [
            str(item["id"])
            for item in results
        ]

        self.assertIn(
            str(donation.id),
            donation_ids,
        )

    def test_donation_list_can_be_filtered_by_status(
        self,
    ):
        donation = self.create_donation_using_api()

        # Status filtering is available only when users
        # request their own donation history.
        self.client.force_authenticate(self.donor)

        response = self.client.get(
            "/api/donations/",
            {
                "mine": "true",
                "status": Donation.Status.AVAILABLE,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        results = response.data.get(
            "results",
            response.data,
        )

        donation_ids = [
            str(item["id"])
            for item in results
        ]

        self.assertIn(
            str(donation.id),
            donation_ids,
        )

    def test_owner_can_view_donation_details(self):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(self.donor)

        response = self.client.get(
            f"/api/donations/{donation.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(donation.id),
        )

    def test_owner_can_create_new_revision(self):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            (
                f"/api/donations/{donation.id}/"
                "revisions/"
            ),
            self.valid_payload(
                food_name="Updated Vegetable Rice",
                quantity="30.000",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        current_revisions = donation.revisions.filter(
            is_current=True
        )

        self.assertEqual(
            current_revisions.count(),
            1,
        )

        current_revision = current_revisions.get()

        self.assertEqual(
            current_revision.food_name,
            "Updated Vegetable Rice",
        )

        self.assertEqual(
            current_revision.quantity,
            Decimal("30.000"),
        )

        self.assertEqual(current_revision.number, 2)

        old_revision = donation.revisions.get(number=1)

        self.assertFalse(old_revision.is_current)

    def test_another_donor_cannot_edit_donation(self):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(
            self.second_donor
        )

        response = self.client.post(
            (
                f"/api/donations/{donation.id}/"
                "revisions/"
            ),
            self.valid_payload(
                food_name="Unauthorized edit"
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

        self.assertEqual(
            donation.revisions.count(),
            1,
        )

    def test_owner_can_cancel_available_donation(self):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            f"/api/donations/{donation.id}/cancel/",
            {
                "reason": (
                    "Food is no longer available."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        donation.refresh_from_db()

        self.assertEqual(
            donation.status,
            Donation.Status.CANCELLED,
        )

    def test_another_donor_cannot_cancel_donation(
        self,
    ):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(
            self.second_donor
        )

        response = self.client.post(
            f"/api/donations/{donation.id}/cancel/",
            {
                "reason": (
                    "Unauthorized cancellation."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

        donation.refresh_from_db()

        self.assertEqual(
            donation.status,
            Donation.Status.AVAILABLE,
        )

    def test_cancellation_creates_status_history(
        self,
    ):
        donation = self.create_donation_using_api()

        initial_count = (
            DonationStatusHistory.objects.filter(
                donation=donation
            ).count()
        )

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            f"/api/donations/{donation.id}/cancel/",
            {
                "reason": (
                    "Donation withdrawn during testing."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        final_count = (
            DonationStatusHistory.objects.filter(
                donation=donation
            ).count()
        )

        self.assertGreater(
            final_count,
            initial_count,
        )

    def test_expired_donation_cannot_receive_request(
        self,
    ):
        now = timezone.now()

        donation = Donation.objects.create(
            donor=self.donor,
            status=Donation.Status.AVAILABLE,
        )

        DonationRevision.objects.create(
            donation=donation,
            number=1,
            is_current=True,
            food_name="Expired Rice",
            category=self.category,
            quantity=Decimal("10.000"),
            unit=DonationRevision.Unit.PORTION,
            description="An expired test listing.",
            storage_condition="Keep covered.",
            prepared_at=now - timedelta(hours=8),
            use_by_at=now - timedelta(hours=2),
            pickup_starts_at=(
                now - timedelta(hours=4)
            ),
            pickup_deadline=(
                now - timedelta(hours=1)
            ),
            pickup_address="Test Address, Nashik",
            pickup_area="Test Area",
            proposed_by=self.donor,
        )

        self.client.force_authenticate(self.receiver)

        response = self.client.post(
            (
                f"/api/donations/{donation.id}/"
                "requests/"
            ),
            {
                "message": (
                    "We would like to receive this food."
                ),
                "proposed_mode": (
                    "RECEIVER_COLLECTION"
                ),
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_409_CONFLICT,
            ],
            response.data,
        )

        donation.refresh_from_db()

        self.assertEqual(
            donation.status,
            Donation.Status.EXPIRED,
        )

    def test_unverified_receiver_cannot_request_donation(
        self,
    ):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(
            self.unverified_receiver
        )

        response = self.client.post(
            (
                f"/api/donations/{donation.id}/"
                "requests/"
            ),
            {
                "message": (
                    "Request from an unverified receiver."
                ),
                "proposed_mode": (
                    "RECEIVER_COLLECTION"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_invalid_image_type_is_rejected(self):
        donation = self.create_donation_using_api()

        invalid_file = SimpleUploadedFile(
            name="malicious.exe",
            content=b"This is not an image.",
            content_type="application/octet-stream",
        )

        self.client.force_authenticate(self.donor)

        response = self.client.post(
            f"/api/donations/{donation.id}/images/",
            {
                "images": [invalid_file],
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn("images", response.data)

    def test_non_owner_cannot_upload_donation_image(
        self,
    ):
        donation = self.create_donation_using_api()

        valid_image = self.create_valid_png()

        self.client.force_authenticate(
            self.second_donor
        )

        response = self.client.post(
            f"/api/donations/{donation.id}/images/",
            {
                "images": [valid_image],
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_owner_can_view_status_history(self):
        donation = self.create_donation_using_api()

        self.client.force_authenticate(self.donor)

        response = self.client.get(
            f"/api/donations/{donation.id}/history/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )