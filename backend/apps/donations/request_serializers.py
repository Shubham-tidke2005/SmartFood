from rest_framework import serializers

from .models import DonationRequest


class DonationRequestCreateSerializer(
    serializers.Serializer
):
    proposed_mode = serializers.ChoiceField(
        choices=DonationRequest.TransportMode.choices
    )


class DonationRequestDecisionSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        default="",
    )


class DonationRequestCancellationSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=3,
        max_length=1000,
    )


class DonationRequestReadSerializer(
    serializers.ModelSerializer
):
    receiver_name = serializers.CharField(
        source="receiver.display_name",
        read_only=True,
    )

    receiver_email = serializers.EmailField(
        source="receiver.email",
        read_only=True,
    )

    donor_name = serializers.CharField(
        source="donation.donor.display_name",
        read_only=True,
    )

    food_name = serializers.CharField(
        source="requested_revision.food_name",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="requested_revision.category.name",
        read_only=True,
    )

    quantity = serializers.DecimalField(
        source="requested_revision.quantity",
        max_digits=12,
        decimal_places=3,
        read_only=True,
    )

    unit = serializers.CharField(
        source="requested_revision.unit",
        read_only=True,
    )

    pickup_deadline = serializers.DateTimeField(
        source="requested_revision.pickup_deadline",
        read_only=True,
    )

    class Meta:
        model = DonationRequest

        fields = [
            "id",
            "donation",
            "receiver",
            "receiver_name",
            "receiver_email",
            "donor_name",
            "requested_revision",
            "food_name",
            "category_name",
            "quantity",
            "unit",
            "status",
            "proposed_mode",
            "expires_at",
            "decided_at",
            "reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields