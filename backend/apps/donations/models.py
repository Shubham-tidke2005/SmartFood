import uuid

from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q


def donation_image_path(instance, filename):
    extension = Path(filename).suffix.lower()

    return (
        f"donations/"
        f"{instance.revision.donation_id}/"
        f"{uuid.uuid4().hex}{extension}"
    )


class FoodCategory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    code = models.SlugField(
        max_length=64,
        unique=True,
    )

    name = models.CharField(
        max_length=100,
    )

    active = models.BooleanField(
        default=True,
    )

    requires_preparation_time = models.BooleanField(
        default=False,
    )

    requires_use_by = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "food_categories"
        ordering = ["name"]
        verbose_name_plural = "Food categories"

    def __str__(self):
        return self.name


class Donation(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        PICKED_UP = "PICKED_UP", "Picked up"
        DELIVERED = "DELIVERED", "Delivered"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donations",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )

    custody_hold = models.BooleanField(
        default=False,
    )

    published_at = models.DateTimeField(
        auto_now_add=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "donations"
        ordering = ["-published_at"]

    def __str__(self):
        return f"Donation {self.id}"


class DonationRevision(models.Model):
    class Unit(models.TextChoices):
        KG = "KG", "Kilogram"
        LITRE = "LITRE", "Litre"
        PORTION = "PORTION", "Portion"
        PACKAGE = "PACKAGE", "Package"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        related_name="revisions",
    )

    number = models.PositiveIntegerField()

    is_current = models.BooleanField(
        default=True,
    )

    food_name = models.CharField(
        max_length=160,
    )

    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.PROTECT,
        related_name="donation_revisions",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
    )

    description = models.TextField(
        blank=True,
    )

    storage_condition = models.CharField(
        max_length=100,
        blank=True,
    )

    pickup_address = models.TextField()

    pickup_starts_at = models.DateTimeField()

    pickup_deadline = models.DateTimeField(
        db_index=True,
    )

    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proposed_donation_revisions",
    )

    prepared_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    use_by_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    pickup_area = models.CharField(
        max_length=100,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "donation_revisions"

        ordering = [
            "donation",
            "-number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "donation",
                    "number",
                ],
                name="unique_donation_revision_number",
            ),
            models.UniqueConstraint(
                fields=["donation"],
                condition=Q(is_current=True),
                name="one_current_revision_per_donation",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="donation_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    pickup_deadline__gt=models.F(
                        "pickup_starts_at"
                    )
                ),
                name="pickup_deadline_after_start",
            ),
        ]

    def __str__(self):
        return (
            f"{self.food_name} — "
            f"revision {self.number}"
        )


class DonationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    class TransportMode(models.TextChoices):
        RECEIVER_COLLECTION = (
            "RECEIVER_COLLECTION",
            "Receiver collection",
        )
        DONOR_DELIVERY = (
            "DONOR_DELIVERY",
            "Donor delivery",
        )
        VOLUNTEER_DELIVERY = (
            "VOLUNTEER_DELIVERY",
            "Volunteer delivery",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        related_name="requests",
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donation_requests",
    )

    requested_revision = models.ForeignKey(
        DonationRevision,
        on_delete=models.PROTECT,
        related_name="requests",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    proposed_mode = models.CharField(
        max_length=30,
        choices=TransportMode.choices,
    )

    expires_at = models.DateTimeField()

    decided_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "donation_requests"
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "donation",
                    "receiver",
                ],
                condition=Q(
                    status__in=[
                        "PENDING",
                        "APPROVED",
                    ]
                ),
                name=(
                    "one_active_request_per_receiver_donation"
                ),
            ),
            models.UniqueConstraint(
                fields=["donation"],
                condition=Q(status="APPROVED"),
                name="one_approved_request_per_donation",
            ),
        ]

    def __str__(self):
        return (
            f"{self.receiver.email} → "
            f"{self.donation_id} → "
            f"{self.status}"
        )


class DonationImage(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    revision = models.ForeignKey(
        DonationRevision,
        on_delete=models.PROTECT,
        related_name="images",
    )

    image = models.ImageField(
        upload_to=donation_image_path,
        max_length=500,
    )

    original_name = models.CharField(
        max_length=255,
    )

    mime_type = models.CharField(
        max_length=100,
    )

    size_bytes = models.PositiveIntegerField()

    position = models.PositiveSmallIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "donation_images"
        ordering = ["position", "created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "revision",
                    "position",
                ],
                name="unique_image_position_per_revision",
            ),
        ]

    def __str__(self):
        return self.original_name


class DonationStatusHistory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        related_name="status_history",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="donation_history_actions",
        null=True,
        blank=True,
    )

    event_type = models.CharField(
        max_length=50,
    )

    from_status = models.CharField(
        max_length=20,
        blank=True,
    )

    to_status = models.CharField(
        max_length=20,
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "donation_status_history"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.donation_id}: "
            f"{self.from_status} → "
            f"{self.to_status}"
        )