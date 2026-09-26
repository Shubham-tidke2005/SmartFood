from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import IsAdministrator

from .models import (
    VerificationDocument,
    VerificationHistory,
    VerificationSubmission,
)
from .serializers import (
    SuspensionSerializer,
    VerificationHistorySerializer,
    VerificationReviewSerializer,
    VerificationSubmissionCreateSerializer,
    VerificationSubmissionReadSerializer,
)


UserModel = get_user_model()


def user_is_administrator(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and user.role == User.Role.ADMIN
        and user.is_staff
    )


class VerificationListCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get(self, request):
        queryset = (
            VerificationSubmission.objects
            .select_related(
                "user",
                "reviewer",
            )
            .prefetch_related("documents")
        )

        if not user_is_administrator(request.user):
            queryset = queryset.filter(
                user=request.user
            )

        serializer = VerificationSubmissionReadSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(serializer.data)

    def post(self, request):
        user = request.user

        if user.role == User.Role.ADMIN:
            return Response(
                {
                    "detail": (
                        "Administrator accounts do not submit "
                        "participant verification."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.contact_verified_at is None:
            return Response(
                {
                    "detail": (
                        "Verify your contact before submitting "
                        "participant verification."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            user.verification_status
            == User.VerificationStatus.VERIFIED
        ):
            return Response(
                {
                    "detail": (
                        "This participant is already verified."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if (
            user.verification_status
            == User.VerificationStatus.SUSPENDED
        ):
            return Response(
                {
                    "detail": (
                        "A suspended participant cannot submit "
                        "verification until an administrator "
                        "reopens verification."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = (
            VerificationSubmissionCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data

        documents = validated_data.pop("documents")
        document_types = validated_data.pop(
            "document_types"
        )

        with transaction.atomic():
            locked_user = (
                UserModel.objects
                .select_for_update()
                .get(pk=user.pk)
            )

            pending_exists = (
                VerificationSubmission.objects.filter(
                    user=locked_user,
                    status=(
                        VerificationSubmission.Status.PENDING
                    ),
                ).exists()
            )

            if pending_exists:
                return Response(
                    {
                        "detail": (
                            "A verification submission is "
                            "already pending."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            maximum_attempt = (
                VerificationSubmission.objects.filter(
                    user=locked_user
                ).aggregate(
                    maximum=Max("attempt")
                )["maximum"]
                or 0
            )

            previous_status = (
                locked_user.verification_status
            )

            submission = (
                VerificationSubmission.objects.create(
                    user=locked_user,
                    attempt=maximum_attempt + 1,
                    status=(
                        VerificationSubmission.Status.PENDING
                    ),
                    submitted_details={
                        "legal_name": validated_data[
                            "legal_name"
                        ],
                        "organization_name": (
                            validated_data.get(
                                "organization_name",
                                "",
                            )
                        ),
                        "registration_identifier": (
                            validated_data.get(
                                "registration_identifier",
                                "",
                            )
                        ),
                        "address": validated_data["address"],
                        "role": locked_user.role,
                    },
                )
            )

            for document_type, uploaded_file in zip(
                document_types,
                documents,
                strict=True,
            ):
                VerificationDocument.objects.create(
                    submission=submission,
                    document_type=document_type,
                    file=uploaded_file,
                    original_name=Path(
                        uploaded_file.name
                    ).name,
                    mime_type=uploaded_file.content_type,
                    size_bytes=uploaded_file.size,
                )

            locked_user.verification_status = (
                User.VerificationStatus.PENDING
            )

            locked_user.save(
                update_fields=[
                    "verification_status",
                ]
            )

            VerificationHistory.objects.create(
                user=locked_user,
                submission=submission,
                actor=locked_user,
                action=(
                    VerificationHistory.Action.SUBMITTED
                ),
                from_status=previous_status,
                to_status=(
                    User.VerificationStatus.PENDING
                ),
                reason="Verification submitted.",
            )

        output = VerificationSubmissionReadSerializer(
            submission,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class VerificationDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, submission_id):
        queryset = (
            VerificationSubmission.objects
            .select_related(
                "user",
                "reviewer",
            )
            .prefetch_related("documents")
        )

        if not user_is_administrator(request.user):
            queryset = queryset.filter(
                user=request.user
            )

        submission = get_object_or_404(
            queryset,
            pk=submission_id,
        )

        serializer = VerificationSubmissionReadSerializer(
            submission,
            context={
                "request": request,
            },
        )

        return Response(serializer.data)


class VerificationDocumentDownloadView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, document_id):
        queryset = (
            VerificationDocument.objects
            .select_related(
                "submission",
                "submission__user",
            )
        )

        if not user_is_administrator(request.user):
            queryset = queryset.filter(
                submission__user=request.user
            )

        document = get_object_or_404(
            queryset,
            pk=document_id,
        )

        if not document.file:
            return Response(
                {
                    "detail": "Document file is unavailable.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=document.original_name,
            content_type=document.mime_type,
        )


class ApproveVerificationView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    def post(self, request, submission_id):
        serializer = VerificationReviewSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data["reason"]

        with transaction.atomic():
            submission = (
                VerificationSubmission.objects
                .select_for_update()
                .select_related("user")
                .get(pk=submission_id)
            )

            if (
                submission.status
                != VerificationSubmission.Status.PENDING
            ):
                return Response(
                    {
                        "detail": (
                            "Only a pending verification can "
                            "be approved."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            participant = (
                UserModel.objects
                .select_for_update()
                .get(pk=submission.user_id)
            )

            previous_status = (
                participant.verification_status
            )

            submission.status = (
                VerificationSubmission.Status.APPROVED
            )
            submission.reviewer = request.user
            submission.reviewed_at = timezone.now()
            submission.reason = reason

            submission.save(
                update_fields=[
                    "status",
                    "reviewer",
                    "reviewed_at",
                    "reason",
                    "updated_at",
                ]
            )

            participant.verification_status = (
                User.VerificationStatus.VERIFIED
            )

            participant.save(
                update_fields=[
                    "verification_status",
                ]
            )

            VerificationHistory.objects.create(
                user=participant,
                submission=submission,
                actor=request.user,
                action=(
                    VerificationHistory.Action.APPROVED
                ),
                from_status=previous_status,
                to_status=(
                    User.VerificationStatus.VERIFIED
                ),
                reason=reason,
            )

        return Response(
            VerificationSubmissionReadSerializer(
                submission,
                context={
                    "request": request,
                },
            ).data
        )


class RejectVerificationView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    def post(self, request, submission_id):
        serializer = VerificationReviewSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data["reason"]

        with transaction.atomic():
            submission = (
                VerificationSubmission.objects
                .select_for_update()
                .select_related("user")
                .get(pk=submission_id)
            )

            if (
                submission.status
                != VerificationSubmission.Status.PENDING
            ):
                return Response(
                    {
                        "detail": (
                            "Only a pending verification can "
                            "be rejected."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            participant = (
                UserModel.objects
                .select_for_update()
                .get(pk=submission.user_id)
            )

            previous_status = (
                participant.verification_status
            )

            submission.status = (
                VerificationSubmission.Status.REJECTED
            )
            submission.reviewer = request.user
            submission.reviewed_at = timezone.now()
            submission.reason = reason

            submission.save(
                update_fields=[
                    "status",
                    "reviewer",
                    "reviewed_at",
                    "reason",
                    "updated_at",
                ]
            )

            participant.verification_status = (
                User.VerificationStatus.REJECTED
            )

            participant.save(
                update_fields=[
                    "verification_status",
                ]
            )

            VerificationHistory.objects.create(
                user=participant,
                submission=submission,
                actor=request.user,
                action=(
                    VerificationHistory.Action.REJECTED
                ),
                from_status=previous_status,
                to_status=(
                    User.VerificationStatus.REJECTED
                ),
                reason=reason,
            )

        return Response(
            VerificationSubmissionReadSerializer(
                submission,
                context={
                    "request": request,
                },
            ).data
        )


class SuspendParticipantView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    def post(self, request, user_id):
        serializer = SuspensionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data["reason"]

        with transaction.atomic():
            participant = get_object_or_404(
                UserModel.objects.select_for_update(),
                pk=user_id,
            )

            if participant.role == User.Role.ADMIN:
                return Response(
                    {
                        "detail": (
                            "Administrator accounts cannot be "
                            "suspended through this endpoint."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            previous_status = (
                participant.verification_status
            )

            if (
                previous_status
                == User.VerificationStatus.SUSPENDED
            ):
                return Response(
                    {
                        "detail": (
                            "The participant is already suspended."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            pending_submission = (
                VerificationSubmission.objects
                .select_for_update()
                .filter(
                    user=participant,
                    status=(
                        VerificationSubmission.Status.PENDING
                    ),
                )
                .first()
            )

            if pending_submission:
                pending_submission.status = (
                    VerificationSubmission.Status.REJECTED
                )
                pending_submission.reviewer = request.user
                pending_submission.reviewed_at = timezone.now()
                pending_submission.reason = (
                    f"Suspended: {reason}"
                )

                pending_submission.save(
                    update_fields=[
                        "status",
                        "reviewer",
                        "reviewed_at",
                        "reason",
                        "updated_at",
                    ]
                )

            participant.verification_status = (
                User.VerificationStatus.SUSPENDED
            )

            participant.save(
                update_fields=[
                    "verification_status",
                ]
            )

            VerificationHistory.objects.create(
                user=participant,
                submission=pending_submission,
                actor=request.user,
                action=(
                    VerificationHistory.Action.SUSPENDED
                ),
                from_status=previous_status,
                to_status=(
                    User.VerificationStatus.SUSPENDED
                ),
                reason=reason,
            )

        return Response(
            {
                "message": "Participant suspended.",
                "user_id": participant.id,
                "verification_status": (
                    participant.verification_status
                ),
            }
        )


class ReopenParticipantVerificationView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    def post(self, request, user_id):
        serializer = SuspensionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data["reason"]

        with transaction.atomic():
            participant = get_object_or_404(
                UserModel.objects.select_for_update(),
                pk=user_id,
            )

            if (
                participant.verification_status
                != User.VerificationStatus.SUSPENDED
            ):
                return Response(
                    {
                        "detail": (
                            "Only a suspended participant can "
                            "be reopened."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            participant.verification_status = (
                User.VerificationStatus.PENDING
            )

            participant.save(
                update_fields=[
                    "verification_status",
                ]
            )

            VerificationHistory.objects.create(
                user=participant,
                actor=request.user,
                action=(
                    VerificationHistory.Action.REOPENED
                ),
                from_status=(
                    User.VerificationStatus.SUSPENDED
                ),
                to_status=(
                    User.VerificationStatus.PENDING
                ),
                reason=reason,
            )

        return Response(
            {
                "message": (
                    "Participant verification reopened."
                ),
                "user_id": participant.id,
                "verification_status": (
                    participant.verification_status
                ),
            }
        )


class VerificationHistoryView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request):
        queryset = (
            VerificationHistory.objects
            .select_related(
                "actor",
                "submission",
                "user",
            )
        )

        if user_is_administrator(request.user):
            user_id = request.query_params.get(
                "user_id"
            )

            if user_id:
                queryset = queryset.filter(
                    user_id=user_id
                )

        else:
            queryset = queryset.filter(
                user=request.user
            )

        serializer = VerificationHistorySerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)