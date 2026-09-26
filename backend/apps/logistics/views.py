from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
)
from apps.donations.services import (
    record_donation_history,
)
from apps.notifications.models import Notification

from .models import (
    DeliveryRecord,
    HandoverRecord,
    ReceiptConfirmation,
)
from .serializers import (
    DeliveryCreateSerializer,
    DeliveryReadSerializer,
    HandoverCreateSerializer,
    HandoverReadSerializer,
    ReceiptCreateSerializer,
    ReceiptReadSerializer,
)
from .services import (
    DIRECT_TRANSPORT_MODES,
    get_locked_approved_request,
    release_capacity_after_receipt,
    schedule_logistics_notifications,
)


def user_is_admin(user):
    return bool(
        user.role == User.Role.ADMIN
        and user.is_staff
    )


def user_can_view_fulfilment(
    user,
    donation,
    donation_request,
):
    return bool(
        user_is_admin(user)
        or donation.donor_id == user.id
        or donation_request.receiver_id == user.id
    )


class DirectFulfilmentDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, donation_id):
        donation = get_object_or_404(
            Donation.objects.select_related("donor"),
            pk=donation_id,
        )

        donation_request = get_object_or_404(
            DonationRequest.objects.select_related(
                "receiver"
            ),
            donation=donation,
            status=DonationRequest.Status.APPROVED,
        )

        if not user_can_view_fulfilment(
            request.user,
            donation,
            donation_request,
        ):
            return Response(
                {
                    "detail": "Donation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        handover = (
            HandoverRecord.objects
            .select_related("confirmed_by")
            .filter(donation=donation)
            .first()
        )

        delivery = (
            DeliveryRecord.objects
            .select_related("delivered_by")
            .filter(donation=donation)
            .first()
        )

        receipt = (
            ReceiptConfirmation.objects
            .select_related("confirmed_by")
            .filter(donation=donation)
            .first()
        )

        return Response(
            {
                "donation_id": str(donation.id),
                "donation_status": donation.status,
                "transport_mode": (
                    donation_request.proposed_mode
                ),
                "handover": (
                    HandoverReadSerializer(
                        handover
                    ).data
                    if handover
                    else None
                ),
                "delivery": (
                    DeliveryReadSerializer(
                        delivery
                    ).data
                    if delivery
                    else None
                ),
                "receipt": (
                    ReceiptReadSerializer(
                        receipt
                    ).data
                    if receipt
                    else None
                ),
            }
        )


class HandoverConfirmView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, donation_id):
        serializer = HandoverCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

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
                            "Only the donor or an "
                            "administrator can confirm "
                            "handover."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                donation.status
                != Donation.Status.RESERVED
            ):
                return Response(
                    {
                        "detail": (
                            "Only a reserved donation can "
                            "be handed over."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            donation_request = (
                get_locked_approved_request(
                    donation
                )
            )

            if donation_request is None:
                return Response(
                    {
                        "detail": (
                            "No approved receiver "
                            "allocation exists."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if (
                donation_request.proposed_mode
                not in DIRECT_TRANSPORT_MODES
            ):
                return Response(
                    {
                        "detail": (
                            "Volunteer delivery must use "
                            "the volunteer workflow."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            existing_handover = (
                HandoverRecord.objects
                .select_for_update()
                .filter(donation=donation)
                .exists()
            )

            if existing_handover:
                return Response(
                    {
                        "detail": (
                            "Handover has already been "
                            "confirmed."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            revision = (
                donation_request.requested_revision
            )

            actual_quantity = (
                serializer.validated_data[
                    "actual_quantity"
                ]
            )

            if actual_quantity > revision.quantity:
                return Response(
                    {
                        "actual_quantity": (
                            "Actual handover quantity cannot "
                            "exceed the listed quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            handover = HandoverRecord.objects.create(
                donation=donation,
                donation_request=donation_request,
                revision=revision,
                confirmed_by=request.user,
                actual_quantity=actual_quantity,
                unit=revision.unit,
                notes=serializer.validated_data[
                    "notes"
                ],
                handed_over_at=timezone.now(),
            )

            previous_status = donation.status

            donation.status = (
                Donation.Status.PICKED_UP
            )
            donation.custody_hold = True

            donation.save(
                update_fields=[
                    "status",
                    "custody_hold",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="HANDOVER_CONFIRMED",
                from_status=previous_status,
                to_status=Donation.Status.PICKED_UP,
                reason=(
                    f"Actual quantity released: "
                    f"{actual_quantity} "
                    f"{revision.unit}."
                ),
            )

            schedule_logistics_notifications(
                [
                    {
                        "recipient_id": (
                            donation_request.receiver_id
                        ),
                        "notification_type": (
                            Notification.Type
                            .HANDOVER_CONFIRMED
                        ),
                        "title": (
                            "Donation handover confirmed"
                        ),
                        "message": (
                            f"{actual_quantity} "
                            f"{revision.unit} was released."
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
            HandoverReadSerializer(handover).data,
            status=status.HTTP_201_CREATED,
        )


class DirectDeliveryRecordView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, donation_id):
        serializer = DeliveryCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

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
                            "Only the donor or an "
                            "administrator can record "
                            "direct delivery."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                donation.status
                != Donation.Status.PICKED_UP
            ):
                return Response(
                    {
                        "detail": (
                            "Handover must be confirmed "
                            "before delivery."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            donation_request = (
                get_locked_approved_request(
                    donation
                )
            )

            if donation_request is None:
                return Response(
                    {
                        "detail": (
                            "No approved receiver "
                            "allocation exists."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if (
                donation_request.proposed_mode
                != DonationRequest.TransportMode
                .DONOR_DELIVERY
            ):
                return Response(
                    {
                        "detail": (
                            "A delivery record is only "
                            "required for donor delivery."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            handover = get_object_or_404(
                HandoverRecord.objects
                .select_for_update(),
                donation=donation,
                donation_request=donation_request,
            )

            if DeliveryRecord.objects.filter(
                donation=donation
            ).exists():
                return Response(
                    {
                        "detail": (
                            "Delivery has already been "
                            "recorded."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            actual_quantity = (
                serializer.validated_data[
                    "actual_quantity"
                ]
            )

            if (
                actual_quantity
                > handover.actual_quantity
            ):
                return Response(
                    {
                        "actual_quantity": (
                            "Delivered quantity cannot "
                            "exceed handover quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            delivery = DeliveryRecord.objects.create(
                donation=donation,
                donation_request=donation_request,
                handover=handover,
                delivered_by=request.user,
                actual_quantity=actual_quantity,
                unit=handover.unit,
                notes=serializer.validated_data[
                    "notes"
                ],
                delivered_at=timezone.now(),
            )

            previous_status = donation.status
            donation.status = (
                Donation.Status.DELIVERED
            )

            donation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="DELIVERY_RECORDED",
                from_status=previous_status,
                to_status=Donation.Status.DELIVERED,
                reason=(
                    f"Donor delivery recorded: "
                    f"{actual_quantity} "
                    f"{handover.unit}."
                ),
            )

            schedule_logistics_notifications(
                [
                    {
                        "recipient_id": (
                            donation_request.receiver_id
                        ),
                        "notification_type": (
                            Notification.Type
                            .DELIVERY_RECORDED
                        ),
                        "title": (
                            "Donation delivered"
                        ),
                        "message": (
                            "Please inspect the donation "
                            "and confirm receipt."
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
            DeliveryReadSerializer(delivery).data,
            status=status.HTTP_201_CREATED,
        )


class ReceiptConfirmView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, donation_id):
        serializer = ReceiptCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=donation_id,
            )

            donation_request = (
                get_locked_approved_request(
                    donation
                )
            )

            if donation_request is None:
                return Response(
                    {
                        "detail": (
                            "No approved receiver "
                            "allocation exists."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            authorized = (
                donation_request.receiver_id
                == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "Only the approved receiver "
                            "can confirm receipt."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            transport_mode = (
                donation_request.proposed_mode
            )

            if (
                transport_mode
                == DonationRequest.TransportMode
                .RECEIVER_COLLECTION
            ):
                required_status = (
                    Donation.Status.PICKED_UP
                )

            elif (
                transport_mode
                == DonationRequest.TransportMode
                .DONOR_DELIVERY
            ):
                required_status = (
                    Donation.Status.DELIVERED
                )

            else:
                return Response(
                    {
                        "detail": (
                            "Volunteer delivery must use "
                            "the volunteer workflow."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if donation.status != required_status:
                return Response(
                    {
                        "detail": (
                            "The donation has not reached "
                            "the receipt-confirmation stage."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if ReceiptConfirmation.objects.filter(
                donation=donation
            ).exists():
                return Response(
                    {
                        "detail": (
                            "Receipt has already been "
                            "confirmed."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            handover = get_object_or_404(
                HandoverRecord.objects
                .select_for_update(),
                donation=donation,
                donation_request=donation_request,
            )

            delivery = None

            if (
                transport_mode
                == DonationRequest.TransportMode
                .DONOR_DELIVERY
            ):
                delivery = get_object_or_404(
                    DeliveryRecord.objects
                    .select_for_update(),
                    donation=donation,
                    donation_request=donation_request,
                )

                expected_quantity = (
                    delivery.actual_quantity
                )

            else:
                expected_quantity = (
                    handover.actual_quantity
                )

            accepted_quantity = (
                serializer.validated_data[
                    "accepted_quantity"
                ]
            )

            discrepancy_type = (
                serializer.validated_data[
                    "discrepancy_type"
                ]
            )

            discrepancy_notes = (
                serializer.validated_data[
                    "discrepancy_notes"
                ]
            )

            if (
                accepted_quantity
                > expected_quantity
            ):
                return Response(
                    {
                        "accepted_quantity": (
                            "Accepted quantity cannot exceed "
                            "the recorded delivered or "
                            "handover quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                accepted_quantity
                < expected_quantity
                and discrepancy_type
                == ReceiptConfirmation
                .DiscrepancyType.NONE
            ):
                return Response(
                    {
                        "discrepancy_type": (
                            "A discrepancy type is required "
                            "when the accepted quantity is "
                            "lower than the recorded "
                            "quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            receipt = (
                ReceiptConfirmation.objects.create(
                    donation=donation,
                    donation_request=donation_request,
                    handover=handover,
                    delivery=delivery,
                    confirmed_by=request.user,
                    accepted_quantity=(
                        accepted_quantity
                    ),
                    unit=handover.unit,
                    discrepancy_type=(
                        discrepancy_type
                    ),
                    discrepancy_notes=(
                        discrepancy_notes
                    ),
                    received_at=timezone.now(),
                )
            )

            release_capacity_after_receipt(
                donation_request
            )

            previous_status = donation.status

            if accepted_quantity > 0:
                donation.status = (
                    Donation.Status.COMPLETED
                )
                event_type = (
                    "RECEIPT_CONFIRMED"
                )
            else:
                donation.status = (
                    Donation.Status.FAILED
                )
                event_type = (
                    "RECEIPT_REJECTED"
                )

            donation.closed_at = timezone.now()
            donation.custody_hold = False

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "custody_hold",
                    "updated_at",
                ]
            )

            reason = (
                f"Accepted quantity: "
                f"{accepted_quantity} "
                f"{handover.unit}."
            )

            if (
                discrepancy_type
                != ReceiptConfirmation
                .DiscrepancyType.NONE
            ):
                reason += (
                    f" Discrepancy: "
                    f"{discrepancy_type}. "
                    f"{discrepancy_notes}"
                )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type=event_type,
                from_status=previous_status,
                to_status=donation.status,
                reason=reason,
            )

            schedule_logistics_notifications(
                [
                    {
                        "recipient_id": (
                            donation.donor_id
                        ),
                        "notification_type": (
                            Notification.Type
                            .RECEIPT_CONFIRMED
                            if accepted_quantity > 0
                            else Notification.Type
                            .RECEIPT_REJECTED
                        ),
                        "title": (
                            "Donation receipt confirmed"
                            if accepted_quantity > 0
                            else "Donation receipt rejected"
                        ),
                        "message": reason,
                        "data": {
                            "donation_id": str(
                                donation.id
                            ),
                            "request_id": str(
                                donation_request.id
                            ),
                            "has_discrepancy": (
                                discrepancy_type
                                != ReceiptConfirmation
                                .DiscrepancyType.NONE
                            ),
                        },
                    }
                ]
            )

        return Response(
            ReceiptReadSerializer(receipt).data,
            status=status.HTTP_201_CREATED,
        )