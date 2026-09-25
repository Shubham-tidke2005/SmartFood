from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationTests(APITestCase):
    def test_public_registration_cannot_create_admin(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "fake-admin@example.com",
                "display_name": "Fake Admin",
                "mobile": "9999999999",
                "role": "ADMIN",
                "password": "StrongTestPassword@123",
                "password_confirm": (
                    "StrongTestPassword@123"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            User.objects.filter(
                email="fake-admin@example.com"
            ).exists()
        )

    def test_login_returns_access_and_refresh_cookie(self):
        User.objects.create_user(
            email="login@example.com",
            display_name="Login User",
            role=User.Role.RECEIVER,
            password="StrongTestPassword@123",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": "login@example.com",
                "password": "StrongTestPassword@123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "sf_refresh",
            response.cookies,
        )

    def test_profile_endpoint_updates_only_current_user(self):
        receiver = User.objects.create_user(
            email="receiver@example.com",
            display_name="Original Receiver",
            role=User.Role.RECEIVER,
            password="StrongTestPassword@123",
        )

        donor = User.objects.create_user(
            email="donor@example.com",
            display_name="Unchanged Donor",
            role=User.Role.DONOR,
            password="StrongTestPassword@123",
        )

        self.client.force_authenticate(
            user=receiver
        )

        response = self.client.patch(
            reverse("accounts:my-profile"),
            {
                "display_name": "Updated Receiver",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        receiver.refresh_from_db()
        donor.refresh_from_db()

        self.assertEqual(
            receiver.display_name,
            "Updated Receiver",
        )

        self.assertEqual(
            donor.display_name,
            "Unchanged Donor",
        )

    def test_user_cannot_change_own_role(self):
        receiver = User.objects.create_user(
            email="receiver@example.com",
            display_name="Receiver",
            role=User.Role.RECEIVER,
            password="StrongTestPassword@123",
        )

        self.client.force_authenticate(
            user=receiver
        )

        response = self.client.patch(
            reverse("accounts:my-profile"),
            {
                "role": "DONOR",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        receiver.refresh_from_db()

        self.assertEqual(
            receiver.role,
            User.Role.RECEIVER,
        )