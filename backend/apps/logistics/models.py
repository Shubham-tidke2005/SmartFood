import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
)
from apps.receivers.models import ServiceArea


class HandoverRecord(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.PROTECT,
        related_name="handover_record",
    )

    donation_request = models.OneToOneField(
        DonationRequest,
        on_delete=models.PROTECT,
        related_name="handover_record",
    )

    revision = models.ForeignKey(
        DonationRevision,
        on_delete=models.PROTECT,
        related_name="handover_records",
    )

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_handovers",
    )

    actual_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    notes = models.TextField(blank=True)
    handed_over_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "handover_records"
        ordering = ["-handed_over_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(actual_quantity__gt=0),
                name="handover_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"Handover for {self.donation_id}"


class DeliveryRecord(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.PROTECT,
        related_name="delivery_record",
    )

    donation_request = models.OneToOneField(
        DonationRequest,
        on_delete=models.PROTECT,
        related_name="delivery_record",
    )

    handover = models.OneToOneField(
        HandoverRecord,
        on_delete=models.PROTECT,
        related_name="delivery_record",
    )

    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="direct_delivery_records",
    )

    actual_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    notes = models.TextField(blank=True)
    delivered_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "delivery_records"
        ordering = ["-delivered_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(actual_quantity__gt=0),
                name="delivery_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"Delivery for {self.donation_id}"


class ReceiptConfirmation(models.Model):
    class DiscrepancyType(models.TextChoices):
        NONE = "NONE", "No discrepancy"
        SHORTAGE = "SHORTAGE", "Quantity shortage"
        DAMAGE = "DAMAGE", "Damaged food or packaging"
        QUALITY = "QUALITY", "Quality concern"
        WRONG_ITEM = "WRONG_ITEM", "Wrong food item"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.PROTECT,
        related_name="receipt_confirmation",
    )

    donation_request = models.OneToOneField(
        DonationRequest,
        on_delete=models.PROTECT,
        related_name="receipt_confirmation",
    )

    handover = models.OneToOneField(
        HandoverRecord,
        on_delete=models.PROTECT,
        related_name="receipt_confirmation",
    )

    delivery = models.OneToOneField(
        DeliveryRecord,
        on_delete=models.PROTECT,
        related_name="receipt_confirmation",
        null=True,
        blank=True,
    )

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receipt_confirmations",
    )

    accepted_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    discrepancy_type = models.CharField(
        max_length=20,
        choices=DiscrepancyType.choices,
        default=DiscrepancyType.NONE,
    )

    discrepancy_notes = models.TextField(blank=True)
    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receipt_confirmations"
        ordering = ["-received_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(accepted_quantity__gte=0),
                name="accepted_quantity_nonnegative",
            ),
        ]

    @property
    def has_discrepancy(self):
        return (
            self.discrepancy_type
            != self.DiscrepancyType.NONE
        )

    def __str__(self):
        return f"Receipt for {self.donation_id}"


class VolunteerProfile(models.Model):
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"
        BUSY = "BUSY", "Busy"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="volunteer_profile",
    )

    service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="volunteer_profiles",
    )

    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.UNAVAILABLE,
        db_index=True,
    )

    max_service_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default="10.00",
    )

    max_active_tasks = models.PositiveSmallIntegerField(
        default=1,
    )

    operational = models.BooleanField(default=True)
    vehicle_description = models.CharField(
        max_length=160,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "volunteer_profiles"

        constraints = [
            models.CheckConstraint(
                condition=Q(max_service_distance_km__gt=0),
                name="volunteer_distance_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_active_tasks__gt=0),
                name="volunteer_task_limit_positive",
            ),
        ]

    def __str__(self):
        return self.user.display_name


class VolunteerCapacity(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transport_capacities",
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    maximum_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "volunteer_capacities"

        constraints = [
            models.UniqueConstraint(
                fields=["volunteer", "unit"],
                name="unique_volunteer_unit_capacity",
            ),
            models.CheckConstraint(
                condition=Q(maximum_quantity__gt=0),
                name="volunteer_capacity_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.volunteer.email}: "
            f"{self.maximum_quantity} {self.unit}"
        )


class VolunteerAvailability(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="volunteer_availability",
    )

    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
    )

    starts_at = models.TimeField()
    ends_at = models.TimeField()
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "volunteer_availability"
        ordering = ["weekday", "starts_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "volunteer",
                    "weekday",
                    "starts_at",
                    "ends_at",
                ],
                name="unique_volunteer_availability",
            ),
        ]


class VolunteerTask(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        ARRIVED_AT_DONOR = (
            "ARRIVED_AT_DONOR",
            "Arrived at donor",
        )
        PICKED_UP = "PICKED_UP", "Picked up"
        ARRIVED_AT_RECEIVER = (
            "ARRIVED_AT_RECEIVER",
            "Arrived at receiver",
        )
        DELIVERED = "DELIVERED", "Delivered"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.OneToOneField(
        Donation,
        on_delete=models.PROTECT,
        related_name="volunteer_task",
    )

    donation_request = models.OneToOneField(
        DonationRequest,
        on_delete=models.PROTECT,
        related_name="volunteer_task",
    )

    assigned_volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="volunteer_tasks",
        null=True,
        blank=True,
    )

    pickup_service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="pickup_tasks",
        null=True,
        blank=True,
    )

    receiver_service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="receiver_tasks",
    )

    pickup_area = models.CharField(max_length=100)

    required_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    pickup_deadline = models.DateTimeField(
        db_index=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    picked_up_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "volunteer_tasks"
        ordering = ["pickup_deadline"]

        constraints = [
            models.CheckConstraint(
                condition=Q(required_quantity__gt=0),
                name="volunteer_task_quantity_positive",
            ),
        ]

    def __str__(self):
        return (
            f"Task {self.id} — {self.status}"
        )


class VolunteerTaskHistory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    task = models.ForeignKey(
        VolunteerTask,
        on_delete=models.PROTECT,
        related_name="history",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="volunteer_task_actions",
        null=True,
        blank=True,
    )

    event_type = models.CharField(max_length=50)
    from_status = models.CharField(
        max_length=30,
        blank=True,
    )
    to_status = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "volunteer_task_history"
        ordering = ["-created_at"]


class VolunteerFailureReport(models.Model):
    class Stage(models.TextChoices):
        BEFORE_PICKUP = (
            "BEFORE_PICKUP",
            "Before pickup",
        )
        AFTER_PICKUP = (
            "AFTER_PICKUP",
            "After pickup",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    task = models.ForeignKey(
        VolunteerTask,
        on_delete=models.PROTECT,
        related_name="failure_reports",
    )

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="volunteer_failure_reports",
    )

    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
    )

    reason = models.TextField()
    reassign_requested = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "volunteer_failure_reports"
        ordering = ["-created_at"]