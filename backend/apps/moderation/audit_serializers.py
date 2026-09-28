from rest_framework import serializers

from apps.donations.models import Donation

from .audit_models import (
    AuditEvent,
    OutcomeCorrection,
)


class AuditEventSerializer(
    serializers.ModelSerializer
):
    actor_email = serializers.EmailField(
        source="actor.email",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AuditEvent

        fields = [
            "id",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "reason",
            "old_values",
            "new_values",
            "metadata",
            "ip_address",
            "created_at",
        ]

        read_only_fields = fields


class AccountDeactivationSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=5,
        max_length=1000,
        trim_whitespace=True,
    )


class OutcomeCorrectionCreateSerializer(
    serializers.Serializer
):
    new_status = serializers.ChoiceField(
        choices=[
            Donation.Status.COMPLETED,
            Donation.Status.CANCELLED,
            Donation.Status.EXPIRED,
            Donation.Status.FAILED,
        ]
    )

    reason = serializers.CharField(
        min_length=5,
        max_length=2000,
        trim_whitespace=True,
    )


class OutcomeCorrectionReadSerializer(
    serializers.ModelSerializer
):
    corrected_by_email = (
        serializers.EmailField(
            source="corrected_by.email",
            read_only=True,
        )
    )

    class Meta:
        model = OutcomeCorrection

        fields = [
            "id",
            "donation",
            "corrected_by_email",
            "old_status",
            "new_status",
            "old_closed_at",
            "new_closed_at",
            "reason",
            "created_at",
        ]

        read_only_fields = fields