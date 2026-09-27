from django.core.exceptions import FieldError

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsAdministrator,
)
from apps.donations.models import Donation
from apps.logistics.models import (
    VolunteerTask,
)
from apps.moderation.complaints import (
    Complaint,
)


def donation_status_count(status):
    possible_lookups = [
        "status",
        "current_revision__status",
        "active_revision__status",
    ]

    for lookup in possible_lookups:
        try:
            return (
                Donation.objects.filter(
                    **{
                        lookup: status,
                    }
                ).count()
            )
        except FieldError:
            continue

    return 0


class PlatformAnalyticsView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def get(self, request):
        total_users = User.objects.count()

        active_users = (
            User.objects.filter(
                is_active=True,
            ).count()
        )

        verified_users = (
            User.objects.filter(
                verification_status=(
                    User.VerificationStatus.VERIFIED
                ),
                is_active=True,
            ).count()
        )

        role_counts = {
            role_value.lower(): (
                User.objects.filter(
                    role=role_value,
                ).count()
            )
            for role_value, _ in (
                User.Role.choices
            )
        }

        response_data = {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": (
                verified_users
            ),
            "users_by_role": role_counts,

            "total_donations": (
                Donation.objects.count()
            ),
            "completed_donations": (
                donation_status_count(
                    "COMPLETED"
                )
            ),
            "cancelled_donations": (
                donation_status_count(
                    "CANCELLED"
                )
            ),
            "expired_donations": (
                donation_status_count(
                    "EXPIRED"
                )
            ),

            "total_volunteer_tasks": (
                VolunteerTask.objects.count()
            ),
            "open_volunteer_tasks": (
                VolunteerTask.objects.filter(
                    status=(
                        VolunteerTask.Status.OPEN
                    )
                ).count()
            ),
            "completed_volunteer_tasks": (
                VolunteerTask.objects.filter(
                    status=(
                        VolunteerTask
                        .Status.COMPLETED
                    )
                ).count()
            ),

            "open_complaints": (
                Complaint.objects.filter(
                    status=(
                        Complaint.Status.OPEN
                    )
                ).count()
            ),
            "complaints_in_review": (
                Complaint.objects.filter(
                    status=(
                        Complaint
                        .Status.IN_REVIEW
                    )
                ).count()
            ),
        }

        return Response(response_data)