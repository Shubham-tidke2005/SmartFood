import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


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
                    pickup_deadline__gt=models.F("pickup_starts_at"),
                ),
                name="pickup_deadline_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.food_name} — revision {self.number}"