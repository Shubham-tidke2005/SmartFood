from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsVerifiedReceiver,
)
from apps.notifications.models import Notification
from apps.receivers.models import (
    ReceiverProfile,
    ReceiverRequirement,
)

from .models import (
    Donation,
    DonationRequest,
    DonationRevision,
)
from .request_serializers import (
    DonationRequestCancellationSerializer,
    DonationRequestCreateSerializer,
    DonationRequestDecisionSerializer,
    DonationRequestReadSerializer,
)
from .request_services import (
    cancel_approved_request_for_donation,
    get_locked_compatible_requirement,
    get_locked_receiver_profile,
    release_requirement_capacity,
    reserve_requirement_capacity,
    schedule_notifications,
    validate_receiver_allocation_limit,
)
from .serializers import (
    DonationCancellationSerializer,
    DonationReadSerializer,
)
from .services import (
    expire_donation_if_required,
    record_donation_history,
)


def user_is_admin(user):
    return bool(
        user.role == User.Role.ADMIN
        and user.is_staff
    )


def serialize_request(
    donation_request,
):
    return DonationRequestReadSerializer(
        donation_request
    ).data


class DonationRequestListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request):
        queryset = (
            DonationRequest.objects
            .select_related(
                "receiver",
                "donation",
                "donation__donor",
                "requested_revision",
                "requested_revision__category",
            )
        )

        if request.user.role == User.Role.DONOR:
            queryset = queryset.filter(
                donation__donor=request.user
            )

        elif request.user.role == User.Role.RECEIVER:
            queryset = queryset.filter(
                receiver=request.user
            )

        elif not user_is_admin(request.user):
            queryset = queryset.none()

        requested_status = request.query_params.get(
            "status"
        )

        if requested_status:
            valid_statuses = {
                value
                for value, _label
                in DonationRequest.Status.choices
            }

            if requested_status not in valid_statuses:
                return Response(
                    {
                        "status": (
                            "Invalid donation request status."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(
                status=requested_status
            )

        return Response(
            DonationRequestReadSerializer(
                queryset,
                many=True,
            ).data
        )


class DonationRequestCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedReceiver,
    ]

    def post(self, request, donation_id):
        serializer = DonationRequestCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            with transaction.atomic():
                donation = get_object_or_404(
                    Donation.objects
                    .select_for_update(),
                    pk=donation_id,
                )

                expire_donation_if_required(
                    donation
                )

                if (
                    donation.status
                    != Donation.Status.AVAILABLE
                ):
                    return Response(
                        {
                            "detail": (
                                "Only an available donation "
                                "can receive requests."
                            )
                        },
                        status=(
                            status.HTTP_409_CONFLICT
                        ),
                    )

                if donation.donor_id == request.user.id:
                    return Response(
                        {
                            "detail": (
                                "A donor cannot request "
                                "their own donation."
                            )
                        },
                        status=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                    )

                revision = get_object_or_404(
                    DonationRevision.objects,
                    donation=donation,
                    is_current=True,
                )

                profile, profile_error = (
                    get_locked_receiver_profile(
                        request.user
                    )
                )

                if profile_error:
                    return Response(
                        {"detail": profile_error},
                        status=(
                            status.HTTP_409_CONFLICT
                        ),
                    )

                allocation_error = (
                    validate_receiver_allocation_limit(
                        receiver=request.user,
                        profile=profile,
                    )
                )

                if allocation_error:
                    return Response(
                        {"detail": allocation_error},
                        status=(
                            status.HTTP_409_CONFLICT
                        ),
                    )

                requirement, requirement_error = (
                    get_locked_compatible_requirement(
                        receiver=request.user,
                        revision=revision,
                    )
                )

                if requirement_error:
                    return Response(
                        {"detail": requirement_error},
                        status=(
                            status.HTTP_409_CONFLICT
                        ),
                    )

                expires_at = min(
                    revision.pickup_deadline,
                    timezone.now()
                    + timedelta(hours=24),
                )

                donation_request = (
                    DonationRequest.objects.create(
                        donation=donation,
                        receiver=request.user,
                        requested_revision=revision,
                        status=(
                            DonationRequest.Status.PENDING
                        ),
                        proposed_mode=(
                            serializer.validated_data[
                                "proposed_mode"
                            ]
                        ),
                        expires_at=expires_at,
                    )
                )

                record_donation_history(
                    donation=donation,
                    actor=request.user,
                    event_type="REQUEST_SUBMITTED",
                    from_status=donation.status,
                    to_status=donation.status,
                    reason=(
                        "Receiver submitted a "
                        "donation request."
                    ),
                )

                schedule_notifications(
                    [
                        {
                            "recipient_id": (
                                donation.donor_id
                            ),
                            "notification_type": (
                                Notification.Type
                                .REQUEST_SUBMITTED
                            ),
                            "title": (
                                "New donation request"
                            ),
                            "message": (
                                f"{request.user.display_name} "
                                "requested your donation."
                            ),
                            "data": {
                                "donation_id": str(
                                    donation.id
                                ),
                                "request_id": str(
                                    donation_request.id
                                ),
                            },
                        }
                    ]
                )

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "You already have an active "
                        "request for this donation."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            serialize_request(donation_request),
            status=status.HTTP_201_CREATED,
        )


class DonationRequestWithdrawView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedReceiver,
    ]

    def post(self, request, request_id):
        serializer = DonationRequestDecisionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():
            donation_request = get_object_or_404(
                DonationRequest.objects
                .select_for_update()
                .select_related(
                    "donation",
                    "donation__donor",
                ),
                pk=request_id,
                receiver=request.user,
            )

            if (
                donation_request.status
                != DonationRequest.Status.PENDING
            ):
                return Response(
                    {
                        "detail": (
                            "Only a pending request can "
                            "be withdrawn."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            donation_request.status = (
                DonationRequest.Status.WITHDRAWN
            )
            donation_request.decided_at = (
                timezone.now()
            )
            donation_request.reason = (
                serializer.validated_data["reason"]
                or "Withdrawn by receiver."
            )

            donation_request.save(
                update_fields=[
                    "status",
                    "decided_at",
                    "reason",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation_request.donation,
                actor=request.user,
                event_type="REQUEST_WITHDRAWN",
                from_status=(
                    donation_request.donation.status
                ),
                to_status=(
                    donation_request.donation.status
                ),
                reason=donation_request.reason,
            )

            schedule_notifications(
                [
                    {
                        "recipient_id": (
                            donation_request
                            .donation.donor_id
                        ),
                        "notification_type": (
                            Notification.Type
                            .REQUEST_WITHDRAWN
                        ),
                        "title": "Request withdrawn",
                        "message": (
                            f"{request.user.display_name} "
                            "withdrew their request."
                        ),
                        "data": {
                            "donation_id": str(
                                donation_request
                                .donation_id
                            ),
                            "request_id": str(
                                donation_request.id
                            ),
                        },
                    }
                ]
            )

        return Response(
            serialize_request(donation_request)
        )


class DonationRequestApproveView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, request_id):
        request_reference = get_object_or_404(
            DonationRequest.objects.only(
                "id",
                "donation_id",
            ),
            pk=request_id,
        )

        with transaction.atomic():
            # All approvals for the same donation lock
            # this row first. This serializes simultaneous
            # approval attempts.
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=request_reference.donation_id,
            )

            donation_request = get_object_or_404(
                DonationRequest.objects
                .select_for_update()
                .select_related(
                    "receiver",
                    "requested_revision",
                    "requested_revision__category",
                ),
                pk=request_id,
                donation=donation,
            )

            authorized = (
                donation.donor_id == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner or an "
                            "administrator can approve "
                            "this request."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            expire_donation_if_required(donation)

            if (
                donation.status
                != Donation.Status.AVAILABLE
            ):
                return Response(
                    {
                        "detail": (
                            "This donation is no longer "
                            "available."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if (
                donation_request.status
                != DonationRequest.Status.PENDING
            ):
                return Response(
                    {
                        "detail": (
                            "Only a pending request can "
                            "be approved."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if (
                donation_request.expires_at
                <= timezone.now()
            ):
                donation_request.status = (
                    DonationRequest.Status.EXPIRED
                )
                donation_request.decided_at = (
                    timezone.now()
                )
                donation_request.reason = (
                    "The request expired before approval."
                )

                donation_request.save(
                    update_fields=[
                        "status",
                        "decided_at",
                        "reason",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "detail": (
                            "The request has expired."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            current_revision = get_object_or_404(
                DonationRevision.objects,
                donation=donation,
                is_current=True,
            )

            if (
                donation_request.requested_revision_id
                != current_revision.id
            ):
                return Response(
                    {
                        "detail": (
                            "The donation changed after this "
                            "request was submitted. The "
                            "receiver must submit a new "
                            "request."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            existing_approved = (
                DonationRequest.objects
                .select_for_update()
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.APPROVED
                    ),
                )
                .exclude(pk=donation_request.pk)
                .exists()
            )

            if existing_approved:
                return Response(
                    {
                        "detail": (
                            "This donation already has an "
                            "approved receiver."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            profile, profile_error = (
                get_locked_receiver_profile(
                    donation_request.receiver
                )
            )

            if profile_error:
                return Response(
                    {"detail": profile_error},
                    status=status.HTTP_409_CONFLICT,
                )

            allocation_error = (
                validate_receiver_allocation_limit(
                    receiver=(
                        donation_request.receiver
                    ),
                    profile=profile,
                )
            )

            if allocation_error:
                return Response(
                    {"detail": allocation_error},
                    status=status.HTTP_409_CONFLICT,
                )

            requirement, requirement_error = (
                get_locked_compatible_requirement(
                    receiver=(
                        donation_request.receiver
                    ),
                    revision=current_revision,
                )
            )

            if requirement_error:
                return Response(
                    {"detail": requirement_error},
                    status=status.HTTP_409_CONFLICT,
                )

            reserve_requirement_capacity(
                requirement=requirement,
                quantity=current_revision.quantity,
            )

            approval_time = timezone.now()

            donation_request.status = (
                DonationRequest.Status.APPROVED
            )
            donation_request.decided_at = approval_time
            donation_request.reason = (
                "Approved by donation owner."
            )

            donation_request.save(
                update_fields=[
                    "status",
                    "decided_at",
                    "reason",
                    "updated_at",
                ]
            )

            rejected_requests = list(
                DonationRequest.objects
                .select_for_update()
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.PENDING
                    ),
                )
                .exclude(pk=donation_request.pk)
                .values("id", "receiver_id")
            )

            DonationRequest.objects.filter(
                id__in=[
                    item["id"]
                    for item in rejected_requests
                ]
            ).update(
                status=DonationRequest.Status.REJECTED,
                decided_at=approval_time,
                reason=(
                    "Another receiver was approved."
                ),
                updated_at=approval_time,
            )

            previous_status = donation.status
            donation.status = Donation.Status.RESERVED

            donation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="REQUEST_APPROVED",
                from_status=previous_status,
                to_status=Donation.Status.RESERVED,
                reason=(
                    f"Request {donation_request.id} "
                    "approved."
                ),
            )

            notification_events = [
                {
                    "recipient_id": (
                        donation_request.receiver_id
                    ),
                    "notification_type": (
                        Notification.Type
                        .REQUEST_APPROVED
                    ),
                    "title": (
                        "Donation request approved"
                    ),
                    "message": (
                        "Your donation request was "
                        "approved."
                    ),
                    "data": {
                        "donation_id": str(
                            donation.id
                        ),
                        "request_id": str(
                            donation_request.id
                        ),
                    },
                }
            ]

            for rejected_request in rejected_requests:
                notification_events.append(
                    {
                        "recipient_id": (
                            rejected_request[
                                "receiver_id"
                            ]
                        ),
                        "notification_type": (
                            Notification.Type
                            .REQUEST_REJECTED
                        ),
                        "title": (
                            "Donation request closed"
                        ),
                        "message": (
                            "Another receiver was selected "
                            "for this donation."
                        ),
                        "data": {
                            "donation_id": str(
                                donation.id
                            ),
                            "request_id": str(
                                rejected_request["id"]
                            ),
                        },
                    }
                )

            schedule_notifications(
                notification_events
            )

        return Response(
            serialize_request(donation_request)
        )


class DonationRequestRejectView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, request_id):
        serializer = DonationRequestDecisionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        request_reference = get_object_or_404(
            DonationRequest.objects.only(
                "id",
                "donation_id",
            ),
            pk=request_id,
        )

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=request_reference.donation_id,
            )

            donation_request = get_object_or_404(
                DonationRequest.objects
                .select_for_update()
                .select_related("receiver"),
                pk=request_id,
                donation=donation,
            )

            authorized = (
                donation.donor_id == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner or an "
                            "administrator can reject "
                            "this request."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                donation_request.status
                != DonationRequest.Status.PENDING
            ):
                return Response(
                    {
                        "detail": (
                            "Only a pending request can "
                            "be rejected."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            donation_request.status = (
                DonationRequest.Status.REJECTED
            )
            donation_request.decided_at = (
                timezone.now()
            )
            donation_request.reason = (
                serializer.validated_data["reason"]
                or "Rejected by donation owner."
            )

            donation_request.save(
                update_fields=[
                    "status",
                    "decided_at",
                    "reason",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="REQUEST_REJECTED",
                from_status=donation.status,
                to_status=donation.status,
                reason=donation_request.reason,
            )

            schedule_notifications(
                [
                    {
                        "recipient_id": (
                            donation_request.receiver_id
                        ),
                        "notification_type": (
                            Notification.Type
                            .REQUEST_REJECTED
                        ),
                        "title": (
                            "Donation request rejected"
                        ),
                        "message": (
                            donation_request.reason
                        ),
                        "data": {
                            "donation_id": str(
                                donation.id
                            ),
                            "request_id": str(
                                donation_request.id
                            ),
                        },
                    }
                ]
            )

        return Response(
            serialize_request(donation_request)
        )


class DonationArrangementCancelView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, request_id):
        serializer = (
            DonationRequestCancellationSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        request_reference = get_object_or_404(
            DonationRequest.objects.only(
                "id",
                "donation_id",
            ),
            pk=request_id,
        )

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=request_reference.donation_id,
            )

            donation_request = get_object_or_404(
                DonationRequest.objects
                .select_for_update()
                .select_related(
                    "receiver",
                    "requested_revision",
                    "requested_revision__category",
                ),
                pk=request_id,
                donation=donation,
            )

            authorized = (
                donation.donor_id == request.user.id
                or donation_request.receiver_id
                == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "You cannot cancel this "
                            "arrangement."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                donation_request.status
                != DonationRequest.Status.APPROVED
                or donation.status
                != Donation.Status.RESERVED
            ):
                return Response(
                    {
                        "detail": (
                            "Only an approved arrangement "
                            "can be cancelled before pickup."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            reason = serializer.validated_data[
                "reason"
            ]

            release_requirement_capacity(
                donation_request=donation_request
            )

            cancellation_time = timezone.now()

            donation_request.status = (
                DonationRequest.Status.CANCELLED
            )
            donation_request.decided_at = (
                cancellation_time
            )
            donation_request.reason = reason

            donation_request.save(
                update_fields=[
                    "status",
                    "decided_at",
                    "reason",
                    "updated_at",
                ]
            )

            previous_status = donation.status

            if (
                donation_request
                .requested_revision.pickup_deadline
                <= cancellation_time
            ):
                donation.status = (
                    Donation.Status.EXPIRED
                )
                donation.closed_at = (
                    cancellation_time
                )
            else:
                donation.status = (
                    Donation.Status.AVAILABLE
                )
                donation.closed_at = None

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type=(
                    "ARRANGEMENT_CANCELLED"
                ),
                from_status=previous_status,
                to_status=donation.status,
                reason=reason,
            )

            recipient_ids = {
                donation.donor_id,
                donation_request.receiver_id,
            }

            recipient_ids.discard(request.user.id)

            schedule_notifications(
                [
                    {
                        "recipient_id": recipient_id,
                        "notification_type": (
                            Notification.Type
                            .ARRANGEMENT_CANCELLED
                        ),
                        "title": (
                            "Donation arrangement cancelled"
                        ),
                        "message": reason,
                        "data": {
                            "donation_id": str(
                                donation.id
                            ),
                            "request_id": str(
                                donation_request.id
                            ),
                        },
                    }
                    for recipient_id in recipient_ids
                ]
            )

        return Response(
            serialize_request(donation_request)
        )


class DonationCancelView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, donation_id):
        serializer = DonationCancellationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data[
            "reason"
        ]

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=donation_id,
            )

            authorized = (
                donation.donor_id == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner or an "
                            "administrator can cancel it."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            expire_donation_if_required(donation)

            if donation.status not in {
                Donation.Status.AVAILABLE,
                Donation.Status.RESERVED,
            }:
                return Response(
                    {
                        "detail": (
                            "This donation can no longer "
                            "be cancelled."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            previous_status = donation.status

            approved_request = (
                cancel_approved_request_for_donation(
                    donation=donation,
                    actor=request.user,
                    reason=(
                        "Donation cancelled: "
                        f"{reason}"
                    ),
                )
            )

            current_time = timezone.now()

            pending_requests = list(
                DonationRequest.objects
                .select_for_update()
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.PENDING
                    ),
                )
                .values("id", "receiver_id")
            )

            DonationRequest.objects.filter(
                id__in=[
                    item["id"]
                    for item in pending_requests
                ]
            ).update(
                status=DonationRequest.Status.CANCELLED,
                decided_at=current_time,
                reason="Donation cancelled.",
                updated_at=current_time,
            )

            donation.status = (
                Donation.Status.CANCELLED
            )
            donation.closed_at = current_time

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="CANCELLED",
                from_status=previous_status,
                to_status=Donation.Status.CANCELLED,
                reason=reason,
            )

            events = []

            for pending_request in pending_requests:
                events.append(
                    {
                        "recipient_id": (
                            pending_request[
                                "receiver_id"
                            ]
                        ),
                        "notification_type": (
                            Notification.Type
                            .DONATION_CANCELLED
                        ),
                        "title": (
                            "Donation cancelled"
                        ),
                        "message": reason,
                        "data": {
                            "donation_id": str(
                                donation.id
                            ),
                            "request_id": str(
                                pending_request["id"]
                            ),
                        },
                    }
                )

            schedule_notifications(events)

        return Response(
            DonationReadSerializer(
                donation,
                context={
                    "request": request,
                },
            ).data
        )