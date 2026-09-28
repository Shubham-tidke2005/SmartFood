from django.core.exceptions import (
    ObjectDoesNotExist,
)

from apps.accounts.models import User

from .models import DonationRequest


def user_is_administrator(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and user.role == User.Role.ADMIN
        and user.is_staff
    )


def user_can_view_exact_pickup(
    user,
    donation,
):
    if not user.is_authenticated:
        return False

    if user_is_administrator(user):
        return True

    if donation.donor_id == user.id:
        return True

    if (
        user.role == User.Role.RECEIVER
        and donation.requests.filter(
            receiver=user,
            status=(
                DonationRequest.Status.APPROVED
            ),
        ).exists()
    ):
        return True

    if user.role == User.Role.VOLUNTEER:
        try:
            task = donation.volunteer_task
        except ObjectDoesNotExist:
            return False

        return bool(
            task.assigned_volunteer_id
            == user.id
        )

    return False


def user_can_view_donor_contact(
    user,
    donation,
):
    return user_can_view_exact_pickup(
        user,
        donation,
    )