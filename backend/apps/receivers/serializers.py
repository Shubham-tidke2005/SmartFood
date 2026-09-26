from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.donations.models import (
    DonationRevision,
    FoodCategory,
)

from .models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)


class ServiceAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea

        fields = [
            "id",
            "code",
            "name",
        ]

        read_only_fields = fields


class ReceiverProfileSerializer(
    serializers.ModelSerializer
):
    service_area = ServiceAreaSerializer(
        read_only=True
    )

    service_area_id = (
        serializers.PrimaryKeyRelatedField(
            queryset=ServiceArea.objects.filter(
                active=True
            ),
            source="service_area",
            write_only=True,
        )
    )

    class Meta:
        model = ReceiverProfile

        fields = [
            "id",
            "organization_name",
            "address",
            "service_area",
            "service_area_id",
            "max_service_distance_km",
            "max_active_allocations",
            "operational",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ReceiverPreferenceSerializer(
    serializers.ModelSerializer
):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    category_code = serializers.CharField(
        source="category.code",
        read_only=True,
    )

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=FoodCategory.objects.filter(
            active=True
        ),
        source="category",
    )

    class Meta:
        model = ReceiverPreference

        fields = [
            "id",
            "category_id",
            "category_name",
            "category_code",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "category_name",
            "category_code",
            "created_at",
            "updated_at",
        ]


class ReceiverRequirementSerializer(
    serializers.ModelSerializer
):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=FoodCategory.objects.filter(
            active=True
        ),
        source="category",
    )

    remaining_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        read_only=True,
    )

    class Meta:
        model = ReceiverRequirement

        fields = [
            "id",
            "category_id",
            "category_name",
            "unit",
            "quantity_needed",
            "quantity_reserved",
            "remaining_quantity",
            "needed_until",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "category_name",
            "quantity_reserved",
            "remaining_quantity",
            "created_at",
            "updated_at",
        ]

    def validate_quantity_needed(self, quantity):
        if quantity <= 0:
            raise serializers.ValidationError(
                "Quantity needed must be greater than zero."
            )

        return quantity

    def validate_needed_until(self, value):
        if value and value < timezone.localdate():
            raise serializers.ValidationError(
                "The need expiry date cannot be in the past."
            )

        return value


class ReceiverAvailabilitySerializer(
    serializers.ModelSerializer
):
    weekday_name = serializers.CharField(
        source="get_weekday_display",
        read_only=True,
    )

    class Meta:
        model = ReceiverAvailability

        fields = [
            "id",
            "weekday",
            "weekday_name",
            "starts_at",
            "ends_at",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "weekday_name",
            "created_at",
            "updated_at",
        ]


class ReceiverDiscoveryFilterSerializer(
    serializers.Serializer
):
    category_id = serializers.UUIDField(
        required=False
    )

    unit = serializers.ChoiceField(
        choices=DonationRevision.Unit.choices,
        required=False,
    )

    max_distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.10"),
        max_value=Decimal("200.00"),
        required=False,
    )

    pickup_before = serializers.DateTimeField(
        required=False
    )

    ordering = serializers.ChoiceField(
        choices=[
            "deadline",
            "distance",
            "quantity",
            "-quantity",
        ],
        default="deadline",
        required=False,
    )

    page = serializers.IntegerField(
        min_value=1,
        default=1,
        required=False,
    )

    page_size = serializers.IntegerField(
        min_value=1,
        max_value=100,
        default=20,
        required=False,
    )