from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsVerifiedReceiver,
    IsVerifiedVolunteer,
)
from apps.donations.models import (
    Donation,
    DonationRequest,
)
from apps.donations.request_services import (
    release_requirement_capacity,
)
from apps.donations.services import (
    record_donation_history,
)
from apps.notifications.models import Notification

from .models import (
    DeliveryRecord,
    HandoverRecord,
    ReceiptConfirmation,
    VolunteerAvailability,
    VolunteerCapacity,
    VolunteerFailureReport,
    VolunteerProfile,
    VolunteerTask,
)
from .volunteer_serializers import (
    VolunteerAvailabilitySerializer,
    VolunteerCapacitySerializer,
    VolunteerFailureSerializer,
    VolunteerProfileSerializer,
    VolunteerQuantitySerializer,
    VolunteerReasonSerializer,
    VolunteerReceiptSerializer,
    VolunteerTaskSerializer,
)
from .volunteer_services import (
    ACTIVE_TASK_STATUSES,
    distance_km,
    record_task_history,
    refresh_volunteer_status,
    schedule_task_notifications,
    volunteer_is_available,
)


def get_locked_task(task_id):
    return get_object_or_404(
        VolunteerTask.objects
        .select_for_update()
        .select_related(
            "donation",
            "donation__donor",
            "donation_request",
            "donation_request__receiver",
            "donation_request__requested_revision",
            "pickup_service_area",
            "receiver_service_area",
            "assigned_volunteer",
        ),
        pk=task_id,
    )


def ensure_assigned_volunteer(task, user):
    return (
        task.assigned_volunteer_id == user.id
    )


class VolunteerProfileView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def get(self, request):
        profile = get_object_or_404(
            VolunteerProfile.objects.select_related(
                "service_area"
            ),
            user=request.user,
        )

        return Response(
            VolunteerProfileSerializer(
                profile
            ).data
        )

    def put(self, request):
        profile = VolunteerProfile.objects.filter(
            user=request.user
        ).first()

        serializer = VolunteerProfileSerializer(
            profile,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=(
                status.HTTP_200_OK
                if profile
                else status.HTTP_201_CREATED
            ),
        )

    def patch(self, request):
        profile = get_object_or_404(
            VolunteerProfile,
            user=request.user,
        )

        serializer = VolunteerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)


class VolunteerCapacityListCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def get(self, request):
        capacities = VolunteerCapacity.objects.filter(
            volunteer=request.user
        )

        return Response(
            VolunteerCapacitySerializer(
                capacities,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = VolunteerCapacitySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        values = serializer.validated_data

        capacity, created = (
            VolunteerCapacity.objects.update_or_create(
                volunteer=request.user,
                unit=values["unit"],
                defaults={
                    "maximum_quantity": values[
                        "maximum_quantity"
                    ],
                    "active": values.get(
                        "active",
                        True,
                    ),
                },
            )
        )

        return Response(
            VolunteerCapacitySerializer(
                capacity
            ).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class VolunteerAvailabilityListCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def get(self, request):
        windows = VolunteerAvailability.objects.filter(
            volunteer=request.user
        )

        return Response(
            VolunteerAvailabilitySerializer(
                windows,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = VolunteerAvailabilitySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            window = serializer.save(
                volunteer=request.user
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This availability window "
                        "already exists."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            VolunteerAvailabilitySerializer(
                window
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EligibleVolunteerTaskListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def get(self, request):
        profile = get_object_or_404(
            VolunteerProfile.objects.select_related(
                "service_area"
            ),
            user=request.user,
            operational=True,
        )

        if (
            profile.availability_status
            == VolunteerProfile
            .AvailabilityStatus.UNAVAILABLE
            or not volunteer_is_available(request.user)
        ):
            return Response([])

        active_count = VolunteerTask.objects.filter(
            assigned_volunteer=request.user,
            status__in=ACTIVE_TASK_STATUSES,
        ).count()

        if active_count >= profile.max_active_tasks:
            return Response([])

        capacities = {
            capacity.unit: capacity.maximum_quantity
            for capacity
            in VolunteerCapacity.objects.filter(
                volunteer=request.user,
                active=True,
            )
        }

        tasks = (
            VolunteerTask.objects
            .filter(
                status=VolunteerTask.Status.OPEN,
                assigned_volunteer__isnull=True,
                pickup_deadline__gt=timezone.now(),
            )
            .select_related(
                "donation",
                "donation_request",
                "donation_request__receiver",
                "donation_request__requested_revision",
                "pickup_service_area",
                "receiver_service_area",
            )
        )

        results = []

        for task in tasks:
            maximum = capacities.get(task.unit)

            if (
                maximum is None
                or task.required_quantity > maximum
                or task.pickup_service_area is None
            ):
                continue

            pickup_distance = distance_km(
                profile.service_area,
                task.pickup_service_area,
            )

            if (
                pickup_distance
                > float(
                    profile.max_service_distance_km
                )
            ):
                continue

            data = VolunteerTaskSerializer(
                task
            ).data

            data["approx_pickup_distance_km"] = (
                round(pickup_distance, 2)
            )

            data["distance_label"] = (
                f"Approximately "
                f"{pickup_distance:.2f} km "
                "straight-line between area centres"
            )

            results.append(data)

        results.sort(
            key=lambda item: (
                item["pickup_deadline"],
                item["approx_pickup_distance_km"],
            )
        )

        return Response(results)


class MyVolunteerTaskListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def get(self, request):
        tasks = (
            VolunteerTask.objects
            .filter(
                assigned_volunteer=request.user
            )
            .select_related(
                "donation_request",
                "donation_request__receiver",
                "donation_request__requested_revision",
                "receiver_service_area",
            )
        )

        return Response(
            VolunteerTaskSerializer(
                tasks,
                many=True,
            ).data
        )


class VolunteerTaskAcceptView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def post(self, request, task_id):
        with transaction.atomic():
            task = get_locked_task(task_id)

            if (
                task.status
                != VolunteerTask.Status.OPEN
                or task.assigned_volunteer_id
                is not None
            ):
                return Response(
                    {
                        "detail": (
                            "This task is no longer "
                            "available."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if task.pickup_deadline <= timezone.now():
                return Response(
                    {
                        "detail": (
                            "The task pickup deadline "
                            "has passed."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            profile = get_object_or_404(
                VolunteerProfile.objects
                .select_for_update()
                .select_related("service_area"),
                user=request.user,
                operational=True,
            )

            if (
                profile.availability_status
                == VolunteerProfile
                .AvailabilityStatus.UNAVAILABLE
                or not volunteer_is_available(
                    request.user
                )
            ):
                return Response(
                    {
                        "detail": (
                            "The volunteer is not "
                            "currently available."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            active_count = (
                VolunteerTask.objects.filter(
                    assigned_volunteer=request.user,
                    status__in=ACTIVE_TASK_STATUSES,
                ).count()
            )

            if active_count >= profile.max_active_tasks:
                return Response(
                    {
                        "detail": (
                            "The volunteer has reached "
                            "the active-task limit."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            capacity = (
                VolunteerCapacity.objects
                .select_for_update()
                .filter(
                    volunteer=request.user,
                    unit=task.unit,
                    active=True,
                    maximum_quantity__gte=(
                        task.required_quantity
                    ),
                )
                .first()
            )

            if capacity is None:
                return Response(
                    {
                        "detail": (
                            "The volunteer does not have "
                            "sufficient transport capacity."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if task.pickup_service_area is None:
                return Response(
                    {
                        "detail": (
                            "The pickup area is not mapped "
                            "to a supported service area."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            pickup_distance = distance_km(
                profile.service_area,
                task.pickup_service_area,
            )

            if (
                pickup_distance
                > float(
                    profile.max_service_distance_km
                )
            ):
                return Response(
                    {
                        "detail": (
                            "The pickup is outside the "
                            "volunteer's service distance."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            previous_status = task.status
            task.status = VolunteerTask.Status.ASSIGNED
            task.assigned_volunteer = request.user
            task.assigned_at = timezone.now()

            task.save(
                update_fields=[
                    "status",
                    "assigned_volunteer",
                    "assigned_at",
                    "updated_at",
                ]
            )

            record_task_history(
                task=task,
                actor=request.user,
                event_type="TASK_ACCEPTED",
                from_status=previous_status,
                to_status=task.status,
                reason="Volunteer accepted the task.",
            )

            refresh_volunteer_status(profile)

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerTaskStatusView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    transition_map = {
        "arrived-donor": (
            VolunteerTask.Status.ASSIGNED,
            VolunteerTask.Status.ARRIVED_AT_DONOR,
        ),
        "arrived-receiver": (
            VolunteerTask.Status.PICKED_UP,
            VolunteerTask.Status.ARRIVED_AT_RECEIVER,
        ),
    }

    def post(self, request, task_id, action):
        transition = self.transition_map.get(action)

        if transition is None:
            return Response(
                {"detail": "Invalid task action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_status, next_status = transition

        with transaction.atomic():
            task = get_locked_task(task_id)

            if not ensure_assigned_volunteer(
                task,
                request.user,
            ):
                return Response(
                    {
                        "detail": (
                            "Only the assigned volunteer "
                            "can update this task."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if task.status != expected_status:
                return Response(
                    {
                        "detail": (
                            "This task cannot perform the "
                            "requested transition."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            previous_status = task.status
            task.status = next_status

            task.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            record_task_history(
                task=task,
                actor=request.user,
                event_type=action.upper().replace(
                    "-",
                    "_",
                ),
                from_status=previous_status,
                to_status=next_status,
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerPickupView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def post(self, request, task_id):
        serializer = VolunteerQuantitySerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            task = get_locked_task(task_id)
            donation = Donation.objects.select_for_update().get(
                pk=task.donation_id
            )

            if not ensure_assigned_volunteer(
                task,
                request.user,
            ):
                return Response(
                    {
                        "detail": (
                            "Only the assigned volunteer "
                            "can record pickup."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if task.status not in {
                VolunteerTask.Status.ASSIGNED,
                VolunteerTask.Status.ARRIVED_AT_DONOR,
            }:
                return Response(
                    {
                        "detail": (
                            "This task is not ready "
                            "for pickup."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if donation.status != Donation.Status.RESERVED:
                return Response(
                    {
                        "detail": (
                            "The donation is no longer "
                            "reserved."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            quantity = serializer.validated_data[
                "actual_quantity"
            ]

            if quantity > task.required_quantity:
                return Response(
                    {
                        "actual_quantity": (
                            "Pickup quantity cannot exceed "
                            "the allocated quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            handover = HandoverRecord.objects.create(
                donation=donation,
                donation_request=task.donation_request,
                revision=(
                    task.donation_request
                    .requested_revision
                ),
                confirmed_by=request.user,
                actual_quantity=quantity,
                unit=task.unit,
                notes=serializer.validated_data[
                    "notes"
                ],
                handed_over_at=timezone.now(),
            )

            previous_task_status = task.status
            task.status = VolunteerTask.Status.PICKED_UP
            task.picked_up_at = timezone.now()
            task.save(
                update_fields=[
                    "status",
                    "picked_up_at",
                    "updated_at",
                ]
            )

            previous_donation_status = donation.status
            donation.status = Donation.Status.PICKED_UP
            donation.custody_hold = True
            donation.save(
                update_fields=[
                    "status",
                    "custody_hold",
                    "updated_at",
                ]
            )

            record_task_history(
                task=task,
                actor=request.user,
                event_type="PICKED_UP",
                from_status=previous_task_status,
                to_status=task.status,
                reason=(
                    f"Picked up {quantity} "
                    f"{task.unit}."
                ),
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="VOLUNTEER_PICKUP",
                from_status=previous_donation_status,
                to_status=donation.status,
                reason=(
                    f"Volunteer picked up {quantity} "
                    f"{task.unit}."
                ),
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerDeliveryView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def post(self, request, task_id):
        serializer = VolunteerQuantitySerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            task = get_locked_task(task_id)
            donation = Donation.objects.select_for_update().get(
                pk=task.donation_id
            )

            if not ensure_assigned_volunteer(
                task,
                request.user,
            ):
                return Response(
                    {
                        "detail": (
                            "Only the assigned volunteer "
                            "can record delivery."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if task.status not in {
                VolunteerTask.Status.PICKED_UP,
                VolunteerTask.Status.ARRIVED_AT_RECEIVER,
            }:
                return Response(
                    {
                        "detail": (
                            "The task has not reached "
                            "the delivery stage."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            handover = get_object_or_404(
                HandoverRecord.objects.select_for_update(),
                donation=donation,
            )

            quantity = serializer.validated_data[
                "actual_quantity"
            ]

            if quantity > handover.actual_quantity:
                return Response(
                    {
                        "actual_quantity": (
                            "Delivery quantity cannot exceed "
                            "pickup quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            DeliveryRecord.objects.create(
                donation=donation,
                donation_request=task.donation_request,
                handover=handover,
                delivered_by=request.user,
                actual_quantity=quantity,
                unit=task.unit,
                notes=serializer.validated_data[
                    "notes"
                ],
                delivered_at=timezone.now(),
            )

            previous_task_status = task.status
            task.status = VolunteerTask.Status.DELIVERED
            task.delivered_at = timezone.now()
            task.save(
                update_fields=[
                    "status",
                    "delivered_at",
                    "updated_at",
                ]
            )

            previous_donation_status = donation.status
            donation.status = Donation.Status.DELIVERED
            donation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            record_task_history(
                task=task,
                actor=request.user,
                event_type="DELIVERED",
                from_status=previous_task_status,
                to_status=task.status,
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="VOLUNTEER_DELIVERY",
                from_status=previous_donation_status,
                to_status=donation.status,
                reason=(
                    f"Volunteer delivered {quantity} "
                    f"{task.unit}."
                ),
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerReceiptConfirmView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedReceiver,
    ]

    def post(self, request, task_id):
        serializer = VolunteerReceiptSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            task = get_locked_task(task_id)
            donation = Donation.objects.select_for_update().get(
                pk=task.donation_id
            )

            if (
                task.donation_request.receiver_id
                != request.user.id
            ):
                return Response(
                    {
                        "detail": (
                            "Only the approved receiver "
                            "can confirm receipt."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                task.status
                != VolunteerTask.Status.DELIVERED
                or donation.status
                != Donation.Status.DELIVERED
            ):
                return Response(
                    {
                        "detail": (
                            "Delivery must be recorded "
                            "before receipt confirmation."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            handover = get_object_or_404(
                HandoverRecord.objects,
                donation=donation,
            )

            delivery = get_object_or_404(
                DeliveryRecord.objects,
                donation=donation,
            )

            accepted = serializer.validated_data[
                "accepted_quantity"
            ]

            discrepancy_type = (
                serializer.validated_data[
                    "discrepancy_type"
                ]
            )

            notes = serializer.validated_data[
                "discrepancy_notes"
            ]

            if accepted > delivery.actual_quantity:
                return Response(
                    {
                        "accepted_quantity": (
                            "Accepted quantity cannot exceed "
                            "delivered quantity."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                accepted < delivery.actual_quantity
                and discrepancy_type == "NONE"
            ):
                return Response(
                    {
                        "discrepancy_type": (
                            "A discrepancy must be reported "
                            "when less quantity is accepted."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ReceiptConfirmation.objects.create(
                donation=donation,
                donation_request=task.donation_request,
                handover=handover,
                delivery=delivery,
                confirmed_by=request.user,
                accepted_quantity=accepted,
                unit=task.unit,
                discrepancy_type=discrepancy_type,
                discrepancy_notes=notes,
                received_at=timezone.now(),
            )

            release_requirement_capacity(
                donation_request=(
                    task.donation_request
                )
            )

            previous_task_status = task.status
            previous_donation_status = donation.status

            task.status = (
                VolunteerTask.Status.COMPLETED
                if accepted > 0
                else VolunteerTask.Status.FAILED
            )
            task.closed_at = timezone.now()
            task.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            donation.status = (
                Donation.Status.COMPLETED
                if accepted > 0
                else Donation.Status.FAILED
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

            profile = VolunteerProfile.objects.select_for_update().get(
                user=task.assigned_volunteer
            )
            refresh_volunteer_status(profile)

            record_task_history(
                task=task,
                actor=request.user,
                event_type="RECEIPT_CONFIRMED",
                from_status=previous_task_status,
                to_status=task.status,
                reason=(
                    f"Accepted {accepted} {task.unit}."
                ),
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="RECEIPT_CONFIRMED",
                from_status=previous_donation_status,
                to_status=donation.status,
                reason=(
                    f"Accepted {accepted} {task.unit}."
                ),
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerCancelAssignmentView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def post(self, request, task_id):
        serializer = VolunteerReasonSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            task = get_locked_task(task_id)

            if not ensure_assigned_volunteer(
                task,
                request.user,
            ):
                return Response(
                    {
                        "detail": (
                            "Only the assigned volunteer "
                            "can cancel the assignment."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if task.status not in {
                VolunteerTask.Status.ASSIGNED,
                VolunteerTask.Status.ARRIVED_AT_DONOR,
            }:
                return Response(
                    {
                        "detail": (
                            "Assignment can only be "
                            "cancelled before pickup."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            previous_status = task.status
            task.status = VolunteerTask.Status.OPEN
            task.assigned_volunteer = None
            task.assigned_at = None

            task.save(
                update_fields=[
                    "status",
                    "assigned_volunteer",
                    "assigned_at",
                    "updated_at",
                ]
            )

            profile = VolunteerProfile.objects.select_for_update().get(
                user=request.user
            )
            refresh_volunteer_status(profile)

            record_task_history(
                task=task,
                actor=request.user,
                event_type="ASSIGNMENT_CANCELLED",
                from_status=previous_status,
                to_status=task.status,
                reason=serializer.validated_data[
                    "reason"
                ],
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )


class VolunteerFailureReportView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedVolunteer,
    ]

    def post(self, request, task_id):
        serializer = VolunteerFailureSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            task = get_locked_task(task_id)

            if not ensure_assigned_volunteer(
                task,
                request.user,
            ):
                return Response(
                    {
                        "detail": (
                            "Only the assigned volunteer "
                            "can report task failure."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            before_pickup = task.status in {
                VolunteerTask.Status.ASSIGNED,
                VolunteerTask.Status.ARRIVED_AT_DONOR,
            }

            reason = serializer.validated_data[
                "reason"
            ]

            reassign = (
                serializer.validated_data["reassign"]
                and before_pickup
            )

            VolunteerFailureReport.objects.create(
                task=task,
                volunteer=request.user,
                stage=(
                    VolunteerFailureReport.Stage
                    .BEFORE_PICKUP
                    if before_pickup
                    else VolunteerFailureReport.Stage
                    .AFTER_PICKUP
                ),
                reason=reason,
                reassign_requested=reassign,
            )

            previous_status = task.status

            if reassign:
                task.status = VolunteerTask.Status.OPEN
                task.assigned_volunteer = None
                task.assigned_at = None
            else:
                task.status = VolunteerTask.Status.FAILED
                task.closed_at = timezone.now()

                donation = (
                    Donation.objects
                    .select_for_update()
                    .get(pk=task.donation_id)
                )

                donation.status = Donation.Status.FAILED
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

                release_requirement_capacity(
                    donation_request=(
                        task.donation_request
                    )
                )

            task.save()

            profile = VolunteerProfile.objects.select_for_update().get(
                user=request.user
            )
            refresh_volunteer_status(profile)

            record_task_history(
                task=task,
                actor=request.user,
                event_type="FAILURE_REPORTED",
                from_status=previous_status,
                to_status=task.status,
                reason=reason,
            )

        return Response(
            VolunteerTaskSerializer(task).data
        )