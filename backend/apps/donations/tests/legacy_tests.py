from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import FoodCategory


class DonationRolePermissionTests(APITestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(
            code="prepared-meals",
            name="Prepared Meals",
        )

        now = timezone.now()

        self.receiver = User.objects.create_user(
            email="receiver@example.com",
            display_name="Receiver Organization",
            role=User.Role.RECEIVER,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified_at=now,
            password="StrongTestPassword@123",
        )

        self.donor = User.objects.create_user(
            email="donor@example.com",
            display_name="Donor Organization",
            role=User.Role.DONOR,
            verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            contact_verified_at=now,
            password="StrongTestPassword@123",
        )

        self.payload = {
            "food_name": "Vegetable Rice",
            "category_id": str(self.category.id),
            "quantity": "20.000",
            "unit": "PORTION",
            "description": "Synthetic test donation",
            "storage_condition": "Keep covered",
            "pickup_address": "Synthetic Pune address",
            "pickup_starts_at": (
                now + timedelta(hours=1)
            ).isoformat(),
            "pickup_deadline": (
                now + timedelta(hours=4)
            ).isoformat(),
        }

    def test_receiver_cannot_create_donation(self):
        self.client.force_authenticate(
            user=self.receiver
        )

        response = self.client.post(
            reverse("donations:create"),
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_verified_donor_can_create_donation(self):
        self.client.force_authenticate(
            user=self.donor
        )

        response = self.client.post(
            reverse("donations:create"),
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["current_revision"]["food_name"],
            "Vegetable Rice",
        )