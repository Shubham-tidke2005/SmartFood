from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsAdministrator,
)
from apps.donations.models import (
    Donation,
    DonationStatusHistory,
)

from .audit_models import (
    AuditEvent,
    OutcomeCorrection,
)
from .audit_serializers import (
    AccountDeactivationSerializer,
    AuditEventSerializer,
    OutcomeCorrectionCreateSerializer,
    OutcomeCorrectionReadSerializer,
)
from .audit_services import (
    record_audit_event,
)
from .models import VerificationHistory


TERMINAL_DONATION_STATUSES = {
    Donation.Status.COMPLETED,
    Donation.Status.CANCELLED,
    Donation.Status.EXPIRED,
    Donation.Status.FAILED,
}


class AuditEventListView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def get(self, request):
        queryset = (
            AuditEvent.objects
            .select_related("actor")
        )

        action = request.query_params.get(
            "action"
        )
        target_type = (
            request.query_params.get(
                "target_type"
            )
        )
        target_id = (
            request.query_params.get(
                "target_id"
            )
        )

        if action:
            queryset = queryset.filter(
                action=action
            )

        if target_type:
            queryset = queryset.filter(
                target_type=target_type
            )

        if target_id:
            queryset = queryset.filter(
                target_id=target_id
            )

        return Response(
            AuditEventSerializer(
                queryset[:500],
                many=True,
            ).data
        )


class ParticipantDeactivateView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def post(self, request, user_id):
        serializer = (
            AccountDeactivationSerializer(
                data=request.data
            )
        )
        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data[
            "reason"
        ]

        with transaction.atomic():
            participant = get_object_or_404(
                User.objects.select_for_update(),
                pk=user_id,
            )

            if participant.role == User.Role.ADMIN:
                return Response(
                    {
                        "detail": (
                            "Administrator accounts cannot "
                            "be deactivated here."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not participant.is_active:
                return Response(
                    {
                        "detail": (
                            "This account is already "
                            "deactivated."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            old_values = {
                "is_active": (
                    participant.is_active
                ),
                "verification_status": (
                    participant
                    .verification_status
                ),
                "auth_version": (
                    participant.auth_version
                ),
            }

            previous_verification_status = (
                participant.verification_status
            )

            participant.is_active = False
            participant.verification_status = (
                User.VerificationStatus.SUSPENDED
            )
            participant.auth_version += 1

            participant.save(
                update_fields=[
                    "is_active",
                    "verification_status",
                    "auth_version",
                    "updated_at",
                ]
            )

            VerificationHistory.objects.create(
                user=participant,
                actor=request.user,
                action=(
                    VerificationHistory
                    .Action.SUSPENDED
                ),
                from_status=(
                    previous_verification_status
                ),
                to_status=(
                    User.VerificationStatus
                    .SUSPENDED
                ),
                reason=reason,
            )

            record_audit_event(
                action=(
                    AuditEvent.Action
                    .ACCOUNT_DEACTIVATED
                ),
                target_type="accounts.User",
                target_id=participant.id,
                actor=request.user,
                request=request,
                reason=reason,
                old_values=old_values,
                new_values={
                    "is_active": False,
                    "verification_status": (
                        User.VerificationStatus
                        .SUSPENDED
                    ),
                    "auth_version": (
                        participant.auth_version
                    ),
                },
            )

        return Response(
            {
                "message": (
                    "Participant account deactivated."
                ),
                "user_id": participant.id,
                "is_active": participant.is_active,
                "verification_status": (
                    participant
                    .verification_status
                ),
            }
        )


class DonationOutcomeCorrectionView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def get(self, request, donation_id):
        corrections = (
            OutcomeCorrection.objects
            .filter(
                donation_id=donation_id
            )
            .select_related(
                "corrected_by"
            )
        )

        return Response(
            OutcomeCorrectionReadSerializer(
                corrections,
                many=True,
            ).data
        )

    def post(self, request, donation_id):
        serializer = (
            OutcomeCorrectionCreateSerializer(
                data=request.data
            )
        )
        serializer.is_valid(
            raise_exception=True
        )

        new_status = (
            serializer.validated_data[
                "new_status"
            ]
        )
        reason = (
            serializer.validated_data[
                "reason"
            ]
        )

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects
                .select_for_update(),
                pk=donation_id,
            )

            if (
                donation.status
                not in TERMINAL_DONATION_STATUSES
            ):
                return Response(
                    {
                        "detail": (
                            "Only a terminal donation "
                            "outcome can be corrected."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if donation.status == new_status:
                return Response(
                    {
                        "detail": (
                            "The corrected status must "
                            "differ from the current status."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            old_status = donation.status
            old_closed_at = donation.closed_at
            corrected_at = timezone.now()

            donation.status = new_status
            donation.closed_at = corrected_at

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            correction = (
                OutcomeCorrection.objects.create(
                    donation=donation,
                    corrected_by=request.user,
                    old_status=old_status,
                    new_status=new_status,
                    old_closed_at=(
                        old_closed_at
                    ),
                    new_closed_at=(
                        corrected_at
                    ),
                    reason=reason,
                )
            )

            DonationStatusHistory.objects.create(
                donation=donation,
                actor=request.user,
                event_type=(
                    "MANUAL_OUTCOME_CORRECTION"
                ),
                from_status=old_status,
                to_status=new_status,
                reason=reason,
            )

            record_audit_event(
                action=(
                    AuditEvent.Action
                    .OUTCOME_CORRECTED
                ),
                target_type=(
                    "donations.Donation"
                ),
                target_id=donation.id,
                actor=request.user,
                request=request,
                reason=reason,
                old_values={
                    "status": old_status,
                    "closed_at": (
                        old_closed_at.isoformat()
                        if old_closed_at
                        else None
                    ),
                },
                new_values={
                    "status": new_status,
                    "closed_at": (
                        corrected_at.isoformat()
                    ),
                },
                metadata={
                    "correction_id": str(
                        correction.id
                    )
                },
            )

        return Response(
            OutcomeCorrectionReadSerializer(
                correction
            ).data,
            status=status.HTTP_201_CREATED,
        )