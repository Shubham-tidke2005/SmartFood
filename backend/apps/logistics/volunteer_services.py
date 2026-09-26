from math import asin, cos, radians, sin, sqrt

from django.db import transaction
from django.utils import timezone

from apps.donations.models import (
    DonationRequest,
)
from apps.notifications.services import (
    create_notifications,
)
from apps.receivers.models import (
    ReceiverProfile,
    ServiceArea,
)

from .models import (
    VolunteerAvailability,
    VolunteerTask,
    VolunteerTaskHistory,
)


ACTIVE_TASK_STATUSES = [
    VolunteerTask.Status.ASSIGNED,
    VolunteerTask.Status.ARRIVED_AT_DONOR,
    VolunteerTask.Status.PICKED_UP,
    VolunteerTask.Status.ARRIVED_AT_RECEIVER,
]


def normalize_area(value):
    return " ".join(value.strip().lower().split())


def distance_km(area_one, area_two):
    radius = 6371.0088

    lat_one = radians(float(area_one.latitude))
    lon_one = radians(float(area_one.longitude))
    lat_two = radians(float(area_two.latitude))
    lon_two = radians(float(area_two.longitude))

    lat_difference = lat_two - lat_one
    lon_difference = lon_two - lon_one

    value = (
        sin(lat_difference / 2) ** 2
        + cos(lat_one)
        * cos(lat_two)
        * sin(lon_difference / 2) ** 2
    )

    return 2 * radius * asin(sqrt(value))


def volunteer_is_available(volunteer):
    current = timezone.localtime()
    weekday = current.weekday()
    current_time = current.time()

    windows = VolunteerAvailability.objects.filter(
        volunteer=volunteer,
        active=True,
    )

    for window in windows:
        if window.starts_at <= window.ends_at:
            if (
                window.weekday == weekday
                and window.starts_at
                <= current_time
                <= window.ends_at
            ):
                return True
        else:
            if (
                window.weekday == weekday
                and current_time >= window.starts_at
            ):
                return True

            if (
                (window.weekday + 1) % 7 == weekday
                and current_time <= window.ends_at
            ):
                return True

    return False


def record_task_history(
    *,
    task,
    actor,
    event_type,
    from_status,
    to_status,
    reason="",
):
    return VolunteerTaskHistory.objects.create(
        task=task,
        actor=actor,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
    )


def schedule_task_notifications(events):
    frozen_events = [
        {
            **event,
            "recipient_id": str(
                event["recipient_id"]
            ),
        }
        for event in events
    ]

    transaction.on_commit(
        lambda: create_notifications(
            frozen_events
        )
    )


def refresh_volunteer_status(profile):
    active_count = VolunteerTask.objects.filter(
        assigned_volunteer=profile.user,
        status__in=ACTIVE_TASK_STATUSES,
    ).count()

    if (
        profile.availability_status
        == profile.AvailabilityStatus.UNAVAILABLE
    ):
        return

    if active_count >= profile.max_active_tasks:
        profile.availability_status = (
            profile.AvailabilityStatus.BUSY
        )
    else:
        profile.availability_status = (
            profile.AvailabilityStatus.AVAILABLE
        )

    profile.save(
        update_fields=[
            "availability_status",
            "updated_at",
        ]
    )


def create_task_for_approved_request(
    donation_request,
):
    if (
        donation_request.proposed_mode
        != DonationRequest.TransportMode
        .VOLUNTEER_DELIVERY
    ):
        return None

    revision = donation_request.requested_revision

    receiver_profile = (
        ReceiverProfile.objects
        .select_related("service_area")
        .get(user=donation_request.receiver)
    )

    area_value = normalize_area(
        revision.pickup_area
    )

    pickup_area = None

    for service_area in ServiceArea.objects.filter(
        active=True
    ):
        if area_value in {
            normalize_area(service_area.name),
            normalize_area(service_area.code),
        }:
            pickup_area = service_area
            break

    task, created = VolunteerTask.objects.get_or_create(
        donation=donation_request.donation,
        defaults={
            "donation_request": donation_request,
            "pickup_service_area": pickup_area,
            "receiver_service_area": (
                receiver_profile.service_area
            ),
            "pickup_area": revision.pickup_area,
            "required_quantity": revision.quantity,
            "unit": revision.unit,
            "pickup_deadline": (
                revision.pickup_deadline
            ),
            "status": VolunteerTask.Status.OPEN,
        },
    )

    if created:
        record_task_history(
            task=task,
            actor=None,
            event_type="TASK_CREATED",
            from_status="",
            to_status=VolunteerTask.Status.OPEN,
            reason=(
                "Volunteer transport task created."
            ),
        )

    return task