import uuid

from decimal import Decimal

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q

from apps.donations.models import (
    DonationRevision,
    FoodCategory,
)


class ServiceArea(models.Model):
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
        max_length=120,
        unique=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-90")),
            MaxValueValidator(Decimal("90")),
        ],
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-180")),
            MaxValueValidator(Decimal("180")),
        ],
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_areas"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReceiverProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receiver_profile",
    )

    organization_name = models.CharField(
        max_length=180,
    )

    address = models.TextField()

    service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="receiver_profiles",
    )

    max_service_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[
            MinValueValidator(Decimal("0.10")),
            MaxValueValidator(Decimal("200.00")),
        ],
    )

    max_active_allocations = models.PositiveSmallIntegerField(
        default=3,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(20),
        ],
    )

    operational = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receiver_profiles"
        ordering = ["organization_name"]

    def __str__(self):
        return self.organization_name


class ReceiverPreference(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="food_preferences",
    )

    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.PROTECT,
        related_name="receiver_preferences",
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receiver_preferences"
        ordering = ["category__name"]

        constraints = [
            models.UniqueConstraint(
                fields=["receiver", "category"],
                name="unique_receiver_food_preference",
            ),
        ]

    def __str__(self):
        return (
            f"{self.receiver.email} accepts "
            f"{self.category.name}"
        )


class ReceiverRequirement(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="food_requirements",
    )

    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.PROTECT,
        related_name="receiver_requirements",
    )

    unit = models.CharField(
        max_length=20,
        choices=DonationRevision.Unit.choices,
    )

    quantity_needed = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal("0.001")),
        ],
    )

    quantity_reserved = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[
            MinValueValidator(Decimal("0.000")),
        ],
    )

    needed_until = models.DateField(
        null=True,
        blank=True,
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receiver_requirements"
        ordering = ["category__name", "unit"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "receiver",
                    "category",
                    "unit",
                ],
                name="unique_receiver_requirement",
            ),
            models.CheckConstraint(
                condition=Q(quantity_needed__gt=0),
                name="receiver_quantity_needed_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity_reserved__gte=0),
                name="receiver_quantity_reserved_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(
                    quantity_reserved__lte=models.F(
                        "quantity_needed"
                    )
                ),
                name="receiver_reserved_not_above_needed",
            ),
        ]

    @property
    def remaining_quantity(self):
        remaining = (
            self.quantity_needed
            - self.quantity_reserved
        )

        return max(remaining, Decimal("0.000"))

    def __str__(self):
        return (
            f"{self.receiver.email}: "
            f"{self.category.name} "
            f"{self.quantity_needed} {self.unit}"
        )


class ReceiverAvailability(models.Model):
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

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receiving_availability",
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
        db_table = "receiver_availability"
        ordering = ["weekday", "starts_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "receiver",
                    "weekday",
                    "starts_at",
                    "ends_at",
                ],
                name="unique_receiver_availability",
            ),
        ]

    def __str__(self):
        return (
            f"{self.receiver.email}: "
            f"{self.get_weekday_display()} "
            f"{self.starts_at}-{self.ends_at}"
        )