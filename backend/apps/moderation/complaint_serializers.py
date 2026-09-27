from django.contrib.auth import (
    get_user_model,
)

from rest_framework import serializers

from apps.donations.models import Donation

from .complaints import Complaint


User = get_user_model()


class ComplaintSerializer(
    serializers.ModelSerializer
):
    reporter_name = (
        serializers.CharField(
            source="reporter.display_name",
            read_only=True,
        )
    )

    reporter_email = (
        serializers.EmailField(
            source="reporter.email",
            read_only=True,
        )
    )

    assigned_to_name = (
        serializers.CharField(
            source="assigned_to.display_name",
            read_only=True,
            allow_null=True,
        )
    )

    class Meta:
        model = Complaint

        fields = [
            "id",
            "reporter",
            "reporter_name",
            "reporter_email",
            "complaint_type",
            "donation",
            "reported_user",
            "subject",
            "description",
            "status",
            "assigned_to",
            "assigned_to_name",
            "resolution",
            "resolved_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "reporter",
            "reporter_name",
            "reporter_email",
            "status",
            "assigned_to",
            "assigned_to_name",
            "resolution",
            "resolved_at",
            "created_at",
            "updated_at",
        ]

    def validate_subject(self, value):
        normalized_value = value.strip()

        if len(normalized_value) < 5:
            raise serializers.ValidationError(
                "Subject must contain at least 5 characters."
            )

        return normalized_value

    def validate_description(self, value):
        normalized_value = value.strip()

        if len(normalized_value) < 10:
            raise serializers.ValidationError(
                "Description must contain at least 10 characters."
            )

        return normalized_value

    def validate_donation(self, donation):
        request = self.context.get(
            "request"
        )

        if (
            donation is None
            or request is None
        ):
            return donation

        user = request.user

        is_related = (
            donation.donor_id == user.id
            or donation.requests.filter(
                receiver=user,
            ).exists()
        )

        if (
            not is_related
            and not user.is_staff
        ):
            raise serializers.ValidationError(
                "You cannot report an unrelated donation."
            )

        return donation


class ComplaintAdminUpdateSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Complaint

        fields = [
            "status",
            "assigned_to",
            "resolution",
        ]

    def validate_assigned_to(
        self,
        assigned_to,
    ):
        if (
            assigned_to is not None
            and not assigned_to.is_staff
        ):
            raise serializers.ValidationError(
                "Complaints can only be assigned to an administrator."
            )

        return assigned_to

    def validate(self, attrs):
        complaint_status = attrs.get(
            "status",
            self.instance.status,
        )

        resolution = attrs.get(
            "resolution",
            self.instance.resolution,
        )

        if (
            complaint_status
            in {
                Complaint.Status.RESOLVED,
                Complaint.Status.REJECTED,
            }
            and not resolution.strip()
        ):
            raise serializers.ValidationError(
                {
                    "resolution": (
                        "A resolution is required "
                        "when closing a complaint."
                    ),
                }
            )

        return attrs