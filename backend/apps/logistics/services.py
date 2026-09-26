from django.db import transaction

from apps.donations.models import (
    DonationRequest,
)
from apps.donations.request_services import (
    release_requirement_capacity,
)
from apps.notifications.services import (
    create_notifications,
)


DIRECT_TRANSPORT_MODES = {
    DonationRequest.TransportMode.RECEIVER_COLLECTION,
    DonationRequest.TransportMode.DONOR_DELIVERY,
}


def get_locked_approved_request(donation):
    return (
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


def schedule_logistics_notifications(events):
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


def release_capacity_after_receipt(
    donation_request,
):
    return release_requirement_capacity(
        donation_request=donation_request
    )