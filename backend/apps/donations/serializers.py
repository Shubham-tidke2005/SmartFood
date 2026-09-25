from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal
from .models import (
    Donation,
    DonationRevision,
    FoodCategory,
)


class DonationRevisionReadSerializer(
    serializers.ModelSerializer
):
    category = serializers.CharField(
        source="category.name"
    )

    class Meta:
        model = DonationRevision

        fields = [
            "id",
            "number",
            "food_name",
            "category",
            "quantity",
            "unit",
            "description",
            "storage_condition",
            "pickup_address",
            "pickup_starts_at",
            "pickup_deadline",
        ]


class DonationReadSerializer(serializers.ModelSerializer):
    current_revision = serializers.SerializerMethodField()

    class Meta:
        model = Donation

        fields = [
            "id",
            "status",
            "custody_hold",
            "published_at",
            "current_revision",
        ]

    def get_current_revision(self, donation):
        revision = donation.revisions.filter(
            is_current=True
        ).first()

        if revision is None:
            return None

        return DonationRevisionReadSerializer(
            revision
        ).data


class DonationCreateSerializer(serializers.Serializer):
    food_name = serializers.CharField(
        max_length=160
    )

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=FoodCategory.objects.filter(
            active=True
        ),
        source="category",
    )

    quantity = serializers.DecimalField(
    max_digits=12,
    decimal_places=3,
    min_value=Decimal("0.001"),
    )

    unit = serializers.ChoiceField(
        choices=DonationRevision.Unit.choices
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    storage_condition = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    pickup_address = serializers.CharField()

    pickup_starts_at = serializers.DateTimeField()

    pickup_deadline = serializers.DateTimeField()

    def validate(self, attrs):
        if (
            attrs["pickup_deadline"]
            <= attrs["pickup_starts_at"]
        ):
            raise serializers.ValidationError(
                {
                    "pickup_deadline": (
                        "Pickup deadline must be after "
                        "the pickup start time."
                    )
                }
            )

        if attrs["pickup_deadline"] <= timezone.now():
            raise serializers.ValidationError(
                {
                    "pickup_deadline": (
                        "Pickup deadline must be in the future."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        donor = self.context["request"].user

        with transaction.atomic():
            donation = Donation.objects.create(
                donor=donor,
                status=Donation.Status.AVAILABLE,
            )

            DonationRevision.objects.create(
                donation=donation,
                number=1,
                is_current=True,
                proposed_by=donor,
                **validated_data,
            )

        return donation