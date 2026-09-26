from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notifications,
)
from apps.receivers.models import (
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
)
from apps.receivers.services import (
    receiver_is_currently_available,
)

from .models import (
    Donation,
    DonationRequest,
)
from .services import record_donation_history


def schedule_notifications(events):
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


def get_locked_receiver_profile(receiver):
    profile = (
        ReceiverProfile.objects
        .select_for_update()
        .select_related("service_area")
        .filter(
            user=receiver,
            operational=True,
            service_area__active=True,
        )
        .first()
    )

    if profile is None:
        return None, (
            "The receiver does not have an active "
            "operational profile."
        )

    if not receiver_is_currently_available(
        receiver
    ):
        return None, (
            "The receiver is not currently available."
        )

    return profile, None


def get_locked_compatible_requirement(
    *,
    receiver,
    revision,
):
    today = timezone.localdate()

    preference_exists = (
        ReceiverPreference.objects.filter(
            receiver=receiver,
            category=revision.category,
            active=True,
        ).exists()
    )

    if not preference_exists:
        return None, (
            "The receiver does not accept this "
            "food category."
        )

    requirement = (
        ReceiverRequirement.objects
        .select_for_update()
        .filter(
            receiver=receiver,
            category=revision.category,
            unit=revision.unit,
            active=True,
        )
        .filter(
            Q(needed_until__isnull=True)
            | Q(needed_until__gte=today)
        )
        .first()
    )

    if requirement is None:
        return None, (
            "No active matching receiver "
            "requirement exists."
        )

    if (
        requirement.remaining_quantity
        < revision.quantity
    ):
        return None, (
            "The receiver does not have enough "
            "remaining capacity."
        )

    return requirement, None


def validate_receiver_allocation_limit(
    *,
    receiver,
    profile,
):
    active_count = (
        DonationRequest.objects.filter(
            receiver=receiver,
            status=DonationRequest.Status.APPROVED,
            donation__status__in=[
                Donation.Status.RESERVED,
                Donation.Status.PICKED_UP,
                Donation.Status.DELIVERED,
            ],
        )
        .values("donation_id")
        .distinct()
        .count()
    )

    if active_count >= profile.max_active_allocations:
        return (
            "The receiver has reached its active "
            "allocation limit."
        )

    return None


def reserve_requirement_capacity(
    *,
    requirement,
    quantity,
):
    if requirement.remaining_quantity < quantity:
        raise ValueError(
            "Insufficient remaining receiver capacity."
        )

    requirement.quantity_reserved = (
        requirement.quantity_reserved
        + quantity
    )

    requirement.save(
        update_fields=[
            "quantity_reserved",
            "updated_at",
        ]
    )


def release_requirement_capacity(
    *,
    donation_request,
):
    revision = donation_request.requested_revision

    requirement = (
        ReceiverRequirement.objects
        .select_for_update()
        .filter(
            receiver=donation_request.receiver,
            category=revision.category,
            unit=revision.unit,
        )
        .first()
    )

    if requirement is None:
        return None

    requirement.quantity_reserved = max(
        requirement.quantity_reserved
        - revision.quantity,
        Decimal("0.000"),
    )

    requirement.save(
        update_fields=[
            "quantity_reserved",
            "updated_at",
        ]
    )

    return requirement


def cancel_approved_request_for_donation(
    *,
    donation,
    actor,
    reason,
):
    approved_request = (
        DonationRequest.objects
        .select_for_update()
        .select_related(
            "receiver",
            "requested_revision",
            "requested_revision__category",
        )
        .filter(
            donation=donation,
            status=DonationRequest.Status.APPROVED,
        )
        .first()
    )

    if approved_request is None:
        return None

    release_requirement_capacity(
        donation_request=approved_request
    )

    approved_request.status = (
        DonationRequest.Status.CANCELLED
    )
    approved_request.decided_at = timezone.now()
    approved_request.reason = reason

    approved_request.save(
        update_fields=[
            "status",
            "decided_at",
            "reason",
            "updated_at",
        ]
    )

    schedule_notifications(
        [
            {
                "recipient_id": (
                    approved_request.receiver_id
                ),
                "notification_type": (
                    Notification.Type
                    .ARRANGEMENT_CANCELLED
                ),
                "title": (
                    "Donation arrangement cancelled"
                ),
                "message": reason,
                "data": {
                    "donation_id": str(donation.id),
                    "request_id": str(
                        approved_request.id
                    ),
                },
            }
        ]
    )

    return approved_request