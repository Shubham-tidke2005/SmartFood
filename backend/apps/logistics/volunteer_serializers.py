from decimal import Decimal

from rest_framework import serializers

from apps.donations.models import DonationRevision
from apps.receivers.models import ServiceArea

from .models import (
    VolunteerAvailability,
    VolunteerCapacity,
    VolunteerFailureReport,
    VolunteerProfile,
    VolunteerTask,
)


class VolunteerProfileSerializer(
    serializers.ModelSerializer
):
    service_area_name = serializers.CharField(
        source="service_area.name",
        read_only=True,
    )

    service_area_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceArea.objects.filter(active=True),
        source="service_area",
        write_only=True,
    )

    class Meta:
        model = VolunteerProfile

        fields = [
            "id",
            "service_area_id",
            "service_area_name",
            "availability_status",
            "max_service_distance_km",
            "max_active_tasks",
            "operational",
            "vehicle_description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class VolunteerCapacitySerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = VolunteerCapacity

        fields = [
            "id",
            "unit",
            "maximum_quantity",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class VolunteerAvailabilitySerializer(
    serializers.ModelSerializer
):
    weekday_name = serializers.CharField(
        source="get_weekday_display",
        read_only=True,
    )

    class Meta:
        model = VolunteerAvailability

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


class VolunteerTaskSerializer(
    serializers.ModelSerializer
):
    food_name = serializers.CharField(
        source=(
            "donation_request."
            "requested_revision.food_name"
        ),
        read_only=True,
    )

    receiver_name = serializers.CharField(
        source=(
            "donation_request."
            "receiver.display_name"
        ),
        read_only=True,
    )

    assigned_volunteer_name = serializers.CharField(
        source="assigned_volunteer.display_name",
        read_only=True,
        allow_null=True,
    )

    receiver_area = serializers.CharField(
        source="receiver_service_area.name",
        read_only=True,
    )

    class Meta:
        model = VolunteerTask

        fields = [
            "id",
            "donation",
            "donation_request",
            "food_name",
            "receiver_name",
            "assigned_volunteer_name",
            "pickup_area",
            "receiver_area",
            "required_quantity",
            "unit",
            "pickup_deadline",
            "status",
            "assigned_at",
            "picked_up_at",
            "delivered_at",
            "closed_at",
            "created_at",
        ]

        read_only_fields = fields


class VolunteerQuantitySerializer(
    serializers.Serializer
):
    actual_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )

    notes = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        default="",
    )


class VolunteerReasonSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=3,
        max_length=2000,
    )


class VolunteerFailureSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=3,
        max_length=3000,
    )

    reassign = serializers.BooleanField(
        default=True,
        required=False,
    )


class VolunteerReceiptSerializer(
    serializers.Serializer
):
    accepted_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.000"),
    )

    discrepancy_type = serializers.ChoiceField(
        choices=[
            "NONE",
            "SHORTAGE",
            "DAMAGE",
            "QUALITY",
            "WRONG_ITEM",
            "OTHER",
        ],
        default="NONE",
    )

    discrepancy_notes = serializers.CharField(
        max_length=3000,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs):
        if (
            attrs["discrepancy_type"] != "NONE"
            and not attrs["discrepancy_notes"].strip()
        ):
            raise serializers.ValidationError(
                {
                    "discrepancy_notes": (
                        "Notes are required for a "
                        "discrepancy."
                    )
                }
            )

        return attrs