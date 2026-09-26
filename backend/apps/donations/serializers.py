from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User

from .models import (
    Donation,
    DonationImage,
    DonationRequest,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)
from .validators import validate_donation_image


class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory

        fields = [
            "id",
            "code",
            "name",
            "active",
            "requires_preparation_time",
            "requires_use_by",
        ]

        read_only_fields = fields


class DonationImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DonationImage

        fields = [
            "id",
            "original_name",
            "mime_type",
            "size_bytes",
            "position",
            "image_url",
            "created_at",
        ]

        read_only_fields = fields

    def get_image_url(self, donation_image):
        if not donation_image.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                donation_image.image.url
            )

        return donation_image.image.url


class DonationRevisionReadSerializer(
    serializers.ModelSerializer
):
    category = FoodCategorySerializer(
        read_only=True
    )

    images = DonationImageSerializer(
        many=True,
        read_only=True,
    )

    pickup_address = serializers.SerializerMethodField()

    class Meta:
        model = DonationRevision

        fields = [
            "id",
            "number",
            "is_current",
            "food_name",
            "category",
            "quantity",
            "unit",
            "description",
            "prepared_at",
            "use_by_at",
            "storage_condition",
            "pickup_area",
            "pickup_address",
            "pickup_starts_at",
            "pickup_deadline",
            "images",
            "created_at",
        ]

        read_only_fields = fields

    def get_pickup_address(self, revision):
        request = self.context.get("request")

        if request is None:
            return None

        user = request.user
        donation = revision.donation

        if not user.is_authenticated:
            return None

        if (
            user.role == User.Role.ADMIN
            or donation.donor_id == user.id
        ):
            return revision.pickup_address

        related_receiver = (
            donation.requests.filter(
                receiver=user,
                status__in=[
                    DonationRequest.Status.PENDING,
                    DonationRequest.Status.APPROVED,
                ],
            ).exists()
        )

        if related_receiver:
            return revision.pickup_address

        return None


class DonationReadSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(
        source="donor.display_name",
        read_only=True,
    )

    current_revision = serializers.SerializerMethodField()

    class Meta:
        model = Donation

        fields = [
            "id",
            "donor_name",
            "status",
            "custody_hold",
            "published_at",
            "closed_at",
            "current_revision",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_current_revision(self, donation):
        cached_revisions = getattr(
            donation,
            "current_revision_cache",
            None,
        )

        if cached_revisions is not None:
            revision = (
                cached_revisions[0]
                if cached_revisions
                else None
            )

        else:
            revision = (
                donation.revisions
                .filter(is_current=True)
                .select_related("category")
                .prefetch_related("images")
                .first()
            )

        if revision is None:
            return None

        return DonationRevisionReadSerializer(
            revision,
            context=self.context,
        ).data


class DonationWriteSerializer(serializers.Serializer):
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
        default="",
    )

    prepared_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    use_by_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    storage_condition = serializers.CharField(
        max_length=100,
    )

    pickup_area = serializers.CharField(
        max_length=100,
    )

    pickup_address = serializers.CharField(
        max_length=500,
    )

    pickup_starts_at = serializers.DateTimeField()

    pickup_deadline = serializers.DateTimeField()

    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        max_length=5,
        write_only=True,
    )

    def validate_images(self, images):
        for image in images:
            validate_donation_image(image)

        return images

    def validate(self, attrs):
        category = attrs["category"]
        quantity = attrs["quantity"]
        unit = attrs["unit"]
        prepared_at = attrs.get("prepared_at")
        use_by_at = attrs.get("use_by_at")
        pickup_starts_at = attrs["pickup_starts_at"]
        pickup_deadline = attrs["pickup_deadline"]

        current_time = timezone.now()

        if quantity <= 0:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        "Quantity must be greater than zero."
                    )
                }
            )

        if (
            unit
            in {
                DonationRevision.Unit.PORTION,
                DonationRevision.Unit.PACKAGE,
            }
            and quantity != quantity.to_integral_value()
        ):
            raise serializers.ValidationError(
                {
                    "quantity": (
                        "Portion and package quantities must "
                        "be whole numbers."
                    )
                }
            )

        if pickup_starts_at >= pickup_deadline:
            raise serializers.ValidationError(
                {
                    "pickup_deadline": (
                        "Pickup deadline must be after "
                        "the pickup start time."
                    )
                }
            )

        if pickup_deadline <= current_time:
            raise serializers.ValidationError(
                {
                    "pickup_deadline": (
                        "Pickup deadline must be in the future."
                    )
                }
            )

        if (
            pickup_starts_at
            < current_time - timezone.timedelta(minutes=5)
        ):
            raise serializers.ValidationError(
                {
                    "pickup_starts_at": (
                        "Pickup start time cannot be in "
                        "the past."
                    )
                }
            )

        if category.requires_preparation_time:
            if prepared_at is None:
                raise serializers.ValidationError(
                    {
                        "prepared_at": (
                            "Preparation time is required for "
                            "this food category."
                        )
                    }
                )

        if prepared_at and prepared_at > current_time:
            raise serializers.ValidationError(
                {
                    "prepared_at": (
                        "Preparation time cannot be in "
                        "the future."
                    )
                }
            )

        if category.requires_use_by:
            if use_by_at is None:
                raise serializers.ValidationError(
                    {
                        "use_by_at": (
                            "Use-by time is required for "
                            "this food category."
                        )
                    }
                )

        if use_by_at:
            if use_by_at <= current_time:
                raise serializers.ValidationError(
                    {
                        "use_by_at": (
                            "Use-by time must be in the future."
                        )
                    }
                )

            if use_by_at < pickup_deadline:
                raise serializers.ValidationError(
                    {
                        "use_by_at": (
                            "Use-by time must not be before "
                            "the pickup deadline."
                        )
                    }
                )

        return attrs


class DonationFilterSerializer(serializers.Serializer):
    category_id = serializers.UUIDField(
        required=False
    )

    unit = serializers.ChoiceField(
        choices=DonationRevision.Unit.choices,
        required=False,
    )

    min_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
    )

    max_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
    )

    pickup_before = serializers.DateTimeField(
        required=False
    )

    search = serializers.CharField(
        max_length=100,
        required=False,
    )

    status = serializers.ChoiceField(
        choices=Donation.Status.choices,
        required=False,
    )

    mine = serializers.BooleanField(
        required=False,
        default=False,
    )

    ordering = serializers.ChoiceField(
        choices=[
            "newest",
            "deadline",
            "quantity",
            "-quantity",
        ],
        required=False,
        default="newest",
    )

    def validate(self, attrs):
        minimum = attrs.get("min_quantity")
        maximum = attrs.get("max_quantity")

        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise serializers.ValidationError(
                {
                    "max_quantity": (
                        "Maximum quantity must be greater "
                        "than or equal to minimum quantity."
                    )
                }
            )

        return attrs


class DonationCancellationSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=3,
        max_length=1000,
    )


class DonationImageUploadSerializer(
    serializers.Serializer
):
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=5,
    )

    def validate_images(self, images):
        for image in images:
            validate_donation_image(image)

        return images


class DonationStatusHistorySerializer(
    serializers.ModelSerializer
):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = DonationStatusHistory

        fields = [
            "id",
            "event_type",
            "from_status",
            "to_status",
            "reason",
            "actor_email",
            "created_at",
        ]

        read_only_fields = fields

    def get_actor_email(self, history):
        if history.actor is None:
            return None

        return history.actor.email


class DonationRequestCreateSerializer(
    serializers.Serializer
):
    proposed_mode = serializers.ChoiceField(
        choices=DonationRequest.TransportMode.choices
    )


class DonationRequestReadSerializer(
    serializers.ModelSerializer
):
    receiver_email = serializers.EmailField(
        source="receiver.email",
        read_only=True,
    )

    class Meta:
        model = DonationRequest

        fields = [
            "id",
            "donation",
            "receiver_email",
            "requested_revision",
            "status",
            "proposed_mode",
            "expires_at",
            "created_at",
        ]

        read_only_fields = fields