"""Synthetic fixtures. Public workflow tests still call the real HTTP views."""
from datetime import time, timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import (
    APIClient,
    APITestCase,
    APITransactionTestCase,
)

from apps.accounts.models import User
from apps.donations.models import Donation, DonationRequest, DonationRevision, FoodCategory
from apps.logistics.models import (
    HandoverRecord, DeliveryRecord, VolunteerProfile, VolunteerAvailability,
    VolunteerCapacity, VolunteerTask,
)
from apps.receivers.models import (
    ReceiverProfile, ReceiverPreference, ReceiverRequirement,
    ReceiverAvailability, ServiceArea,
)

TEST_PASSWORD = "Step27-test-only@123"


def api_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class ScenarioMixin:
    def setUp(self):
        super().setUp()
        settings_override = override_settings(
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.area = ServiceArea.objects.create(
            code="step27-central", name="Step27 Central",
            latitude="19.997500", longitude="73.789800", active=True,
        )
        self.category = FoodCategory.objects.create(
            code="step27-prepared", name="Step27 Prepared Meals", active=True,
            requires_preparation_time=True, requires_use_by=True,
        )
        self.donor = self.make_user(User.Role.DONOR)
        self.other_donor = self.make_user(User.Role.DONOR)
        self.admin = self.make_user(User.Role.ADMIN, is_staff=True)
        self.receiver = self.make_receiver()
        self.other_receiver = self.make_receiver()
        self.volunteer = self.make_volunteer()

    def make_user(self, role, **overrides):
        fields = dict(
            email=f"step27-{uuid4().hex}@example.test", display_name=f"Test {role}",
            role=role, is_active=True, contact_verified_at=timezone.now(),
            verification_status=User.VerificationStatus.VERIFIED,
        )
        fields.update(overrides)
        return User.objects.create_user(password=TEST_PASSWORD, **fields)

    def make_receiver(self, quantity="20.000", unit="PORTION", **user_fields):
        user = self.make_user(User.Role.RECEIVER, **user_fields)
        ReceiverProfile.objects.create(
            user=user, organization_name=f"Test NGO {user.pk}", address="Private NGO address",
            service_area=self.area, max_service_distance_km="20.00",
            max_active_allocations=3, operational=True,
        )
        ReceiverPreference.objects.create(receiver=user, category=self.category, active=True)
        ReceiverRequirement.objects.create(
            receiver=user, category=self.category, unit=unit, quantity_needed=quantity,
            needed_until=timezone.localdate() + timedelta(days=7), active=True,
        )
        ReceiverAvailability.objects.bulk_create([
            ReceiverAvailability(receiver=user, weekday=day, starts_at=time.min,
                                 ends_at=time.max, active=True)
            for day in range(7)
        ])
        return user

    def make_volunteer(self):
        user = self.make_user(User.Role.VOLUNTEER)
        VolunteerProfile.objects.create(
            user=user, service_area=self.area, availability_status="AVAILABLE",
            max_service_distance_km="20.00", max_active_tasks=1, operational=True,
        )
        VolunteerCapacity.objects.create(
            volunteer=user, unit="PORTION", maximum_quantity="100.000", active=True,
        )
        VolunteerAvailability.objects.bulk_create([
            VolunteerAvailability(volunteer=user, weekday=day, starts_at=time.min,
                                  ends_at=time.max, active=True)
            for day in range(7)
        ])
        return user

    def payload(self, **overrides):
        now = timezone.now()
        data = dict(
            food_name=f"Step27 meals {uuid4().hex[:8]}", category_id=str(self.category.pk),
            quantity="20.000", unit="PORTION", description="Synthetic test listing",
            storage_condition="Keep covered", pickup_area=self.area.name,
            pickup_address="PRIVATE: 123 Test Street, Nashik",
            pickup_starts_at=(now + timedelta(minutes=15)).isoformat(),
            pickup_deadline=(now + timedelta(hours=3)).isoformat(),
            prepared_at=(now - timedelta(minutes=30)).isoformat(),
            use_by_at=(now + timedelta(hours=5)).isoformat(),
        )
        data.update(overrides)
        return data

    def make_donation(self, donor=None, quantity="20.000", unit="PORTION", expired=False):
        donor = donor or self.donor
        donation = Donation.objects.create(donor=donor)
        fields = self.payload(quantity=quantity, unit=unit)
        fields.pop("category_id")
        # Model fixtures use datetime objects, unlike serialized API payloads.
        for field in ("pickup_starts_at", "pickup_deadline", "prepared_at", "use_by_at"):
            from datetime import datetime
            fields[field] = datetime.fromisoformat(fields[field])
        if expired:
            fields["pickup_deadline"] = timezone.now() - timedelta(minutes=1)
            fields["pickup_starts_at"] = fields["pickup_deadline"] - timedelta(hours=1)
        revision = DonationRevision.objects.create(
            donation=donation, category=self.category, proposed_by=donor,
            number=1, is_current=True, **fields,
        )
        revision.quantity = Decimal(revision.quantity)
        return donation, revision

    def make_request(self, donation, receiver=None, mode="RECEIVER_COLLECTION"):
        revision = donation.revisions.get(is_current=True)
        return DonationRequest.objects.create(
            donation=donation, receiver=receiver or self.receiver, requested_revision=revision,
            proposed_mode=mode, expires_at=revision.pickup_deadline,
        )

    def make_allocation(self, receiver=None, mode="RECEIVER_COLLECTION", unit="PORTION"):
        receiver = receiver or self.receiver
        donation, revision = self.make_donation(unit=unit)
        requirement = ReceiverRequirement.objects.get(receiver=receiver, category=self.category, unit=unit)
        requirement.quantity_reserved += revision.quantity
        requirement.save(update_fields=["quantity_reserved"])
        donation.status = Donation.Status.RESERVED
        donation.save(update_fields=["status"])
        allocation = self.make_request(donation, receiver, mode)
        allocation.status = DonationRequest.Status.APPROVED
        allocation.decided_at = timezone.now()
        allocation.save()  # Real signal creates a volunteer task when appropriate.
        return donation, allocation

    def make_delivered(self, receiver=None, volunteer=False):
        mode = "VOLUNTEER_DELIVERY" if volunteer else "DONOR_DELIVERY"
        donation, allocation = self.make_allocation(receiver=receiver, mode=mode)
        actor = self.volunteer if volunteer else self.donor
        handover = HandoverRecord.objects.create(
            donation=donation, donation_request=allocation, revision=allocation.requested_revision,
            confirmed_by=actor, actual_quantity="20.000", unit="PORTION", handed_over_at=timezone.now(),
        )
        DeliveryRecord.objects.create(
            donation=donation, donation_request=allocation, handover=handover,
            delivered_by=actor, actual_quantity="20.000", unit="PORTION", delivered_at=timezone.now(),
        )
        donation.status = Donation.Status.DELIVERED
        donation.custody_hold = True
        donation.save(update_fields=["status", "custody_hold"])
        if volunteer:
            task = VolunteerTask.objects.get(donation=donation)
            task.assigned_volunteer = actor
            task.status = VolunteerTask.Status.DELIVERED
            task.assigned_at = task.picked_up_at = task.delivered_at = timezone.now()
            task.save()
        return donation, allocation

    def post_as(self, user, name, kwargs, payload=None):
        return api_for(user).post(reverse(name, kwargs=kwargs), payload or {}, format="json")

    def assert_status(self, response, expected):
        if hasattr(response, "data"):
            detail = response.data
        elif response.streaming:
            detail = "Streaming response"
        else:
            detail = response.content[:800]
        self.assertEqual(response.status_code, expected, detail)


class SmartFoodAPICase(ScenarioMixin, APITestCase):
    """No tests here: imported safely by the concrete test modules."""


class SmartFoodAPICase(
    ScenarioMixin,
    APITestCase,
):
    """Base class for ordinary API tests."""


class SmartFoodAPITransactionCase(
    ScenarioMixin,
    APITransactionTestCase,
):
    """
    Base class for streaming responses and tests that
    require real transaction boundaries.
    """