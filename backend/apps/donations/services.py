from django.utils import timezone

from .models import (
    Donation,
    DonationStatusHistory,
)


def record_donation_history(
    *,
    donation,
    actor,
    event_type,
    from_status,
    to_status,
    reason="",
):
    return DonationStatusHistory.objects.create(
        donation=donation,
        actor=actor,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
    )


def expire_donation_if_required(
    donation,
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()

    if donation.status != Donation.Status.AVAILABLE:
        return False

    current_revision = donation.revisions.filter(
        is_current=True
    ).first()

    if current_revision is None:
        return False

    if current_revision.pickup_deadline > current_time:
        return False

    previous_status = donation.status

    donation.status = Donation.Status.EXPIRED
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
        actor=None,
        event_type="EXPIRED",
        from_status=previous_status,
        to_status=Donation.Status.EXPIRED,
        reason="Pickup deadline passed before pickup.",
    )

    return True