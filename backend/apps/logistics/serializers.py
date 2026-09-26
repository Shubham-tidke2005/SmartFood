from decimal import Decimal

from rest_framework import serializers

from .models import (
    DeliveryRecord,
    HandoverRecord,
    ReceiptConfirmation,
)


class HandoverCreateSerializer(
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


class DeliveryCreateSerializer(
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


class ReceiptCreateSerializer(
    serializers.Serializer
):
    accepted_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.000"),
    )

    discrepancy_type = serializers.ChoiceField(
        choices=ReceiptConfirmation
        .DiscrepancyType.choices,
        default=(
            ReceiptConfirmation
            .DiscrepancyType.NONE
        ),
    )

    discrepancy_notes = serializers.CharField(
        max_length=3000,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs):
        discrepancy_type = attrs[
            "discrepancy_type"
        ]

        discrepancy_notes = attrs.get(
            "discrepancy_notes",
            "",
        ).strip()

        if (
            discrepancy_type
            != ReceiptConfirmation
            .DiscrepancyType.NONE
            and not discrepancy_notes
        ):
            raise serializers.ValidationError(
                {
                    "discrepancy_notes": (
                        "Notes are required when reporting "
                        "a discrepancy."
                    )
                }
            )

        return attrs


class HandoverReadSerializer(
    serializers.ModelSerializer
):
    confirmed_by_name = serializers.CharField(
        source="confirmed_by.display_name",
        read_only=True,
    )

    class Meta:
        model = HandoverRecord

        fields = [
            "id",
            "donation",
            "donation_request",
            "revision",
            "confirmed_by_name",
            "actual_quantity",
            "unit",
            "notes",
            "handed_over_at",
            "created_at",
        ]

        read_only_fields = fields


class DeliveryReadSerializer(
    serializers.ModelSerializer
):
    delivered_by_name = serializers.CharField(
        source="delivered_by.display_name",
        read_only=True,
    )

    class Meta:
        model = DeliveryRecord

        fields = [
            "id",
            "donation",
            "donation_request",
            "handover",
            "delivered_by_name",
            "actual_quantity",
            "unit",
            "notes",
            "delivered_at",
            "created_at",
        ]

        read_only_fields = fields


class ReceiptReadSerializer(
    serializers.ModelSerializer
):
    confirmed_by_name = serializers.CharField(
        source="confirmed_by.display_name",
        read_only=True,
    )

    has_discrepancy = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = ReceiptConfirmation

        fields = [
            "id",
            "donation",
            "donation_request",
            "handover",
            "delivery",
            "confirmed_by_name",
            "accepted_quantity",
            "unit",
            "discrepancy_type",
            "discrepancy_notes",
            "has_discrepancy",
            "received_at",
            "created_at",
        ]

        read_only_fields = fields


class DirectFulfilmentReadSerializer(
    serializers.Serializer
):
    donation_id = serializers.UUIDField()
    donation_status = serializers.CharField()
    transport_mode = serializers.CharField()
    handover = HandoverReadSerializer(
        allow_null=True
    )
    delivery = DeliveryReadSerializer(
        allow_null=True
    )
    receipt = ReceiptReadSerializer(
        allow_null=True
    )