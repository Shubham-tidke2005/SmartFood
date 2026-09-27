from collections import defaultdict

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
)
from apps.logistics.models import (
    ReceiptConfirmation,
    VolunteerProfile,
    VolunteerTask,
)
from apps.moderation.models import Complaint
from apps.receivers.models import ReceiverProfile

try:
    from apps.recommendations.models import (
        RecommendationRun,
    )
except ImportError:
    RecommendationRun = None



def calculate_percentage(
    numerator,
    denominator,
):
    if denominator <= 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def previous_month(month, difference):
    month_index = (
        month.year * 12
        + month.month
        - 1
        - difference
    )

    year = month_index // 12
    month_number = month_index % 12 + 1

    return month.replace(
        year=year,
        month=month_number,
        day=1,
    )


def build_status_breakdown(queryset):
    rows = (
        queryset
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    return [
        {
            "status": row["status"],
            "count": row["count"],
        }
        for row in rows
    ]


def build_quantity_totals(receipts):
    rows = (
        receipts
        .values("unit")
        .annotate(
            total=Sum("accepted_quantity")
        )
        .order_by("unit")
    )

    return [
        {
            "unit": row["unit"],
            "quantity": str(
                row["total"] or 0
            ),
        }
        for row in rows
    ]


def build_monthly_trend(
    donation_queryset,
    months=6,
):
    current_month = (
        timezone.localdate()
        .replace(day=1)
    )

    month_values = [
        previous_month(
            current_month,
            difference,
        )
        for difference in reversed(
            range(months)
        )
    ]

    start_date = month_values[0]

    created_rows = (
        donation_queryset
        .filter(created_at__date__gte=start_date)
        .annotate(
            month=TruncMonth("created_at")
        )
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    completed_rows = (
        donation_queryset
        .filter(
            status=Donation.Status.COMPLETED,
            closed_at__date__gte=start_date,
        )
        .annotate(
            month=TruncMonth("closed_at")
        )
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    created_map = {}
    completed_map = {}

    for row in created_rows:
        key = row["month"].strftime(
            "%Y-%m"
        )
        created_map[key] = row["count"]

    for row in completed_rows:
        key = row["month"].strftime(
            "%Y-%m"
        )
        completed_map[key] = row["count"]

    return [
        {
            "month": month.strftime(
                "%Y-%m"
            ),
            "label": month.strftime(
                "%b %Y"
            ),
            "created": created_map.get(
                month.strftime("%Y-%m"),
                0,
            ),
            "completed": completed_map.get(
                month.strftime("%Y-%m"),
                0,
            ),
        }
        for month in month_values
    ]


def get_donor_analytics(user):
    donations = Donation.objects.filter(
        donor=user
    )

    total_created = donations.count()

    completed = donations.filter(
        status=Donation.Status.COMPLETED
    ).count()

    active = donations.filter(
        status__in=[
            Donation.Status.AVAILABLE,
            Donation.Status.RESERVED,
            Donation.Status.PICKED_UP,
            Donation.Status.DELIVERED,
        ]
    ).count()

    unsuccessful = donations.filter(
        status__in=[
            Donation.Status.CANCELLED,
            Donation.Status.EXPIRED,
            Donation.Status.FAILED,
        ]
    ).count()

    eligible_outcomes = (
        completed + unsuccessful
    )

    receipts = (
        ReceiptConfirmation.objects
        .filter(
            donation__donor=user,
            donation__status=(
                Donation.Status.COMPLETED
            ),
        )
    )

    discrepancy_count = (
        receipts.exclude(
            discrepancy_type=(
                ReceiptConfirmation
                .DiscrepancyType.NONE
            )
        ).count()
    )

    return {
        "role": User.Role.DONOR,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": {
            "donations_created": total_created,
            "active_donations": active,
            "completed_donations": completed,
            "unsuccessful_donations": unsuccessful,
            "completion_rate": (
                calculate_percentage(
                    completed,
                    eligible_outcomes,
                )
            ),
            "receipt_discrepancies": (
                discrepancy_count
            ),
        },
        "quantity_redistributed": (
            build_quantity_totals(receipts)
        ),
        "status_breakdown": (
            build_status_breakdown(
                donations
            )
        ),
        "monthly_trend": (
            build_monthly_trend(
                donations
            )
        ),
    }


def get_receiver_analytics(user):
    requests = DonationRequest.objects.filter(
        receiver=user
    )

    submitted = requests.count()

    approved = requests.filter(
        status=DonationRequest.Status.APPROVED
    ).count()

    pending = requests.filter(
        status=DonationRequest.Status.PENDING
    ).count()

    completed_donations = (
        Donation.objects.filter(
            requests__receiver=user,
            requests__status=(
                DonationRequest.Status.APPROVED
            ),
            status=Donation.Status.COMPLETED,
        )
        .distinct()
    )

    receipts = (
        ReceiptConfirmation.objects
        .filter(
            donation_request__receiver=user,
            donation__status=(
                Donation.Status.COMPLETED
            ),
        )
    )

    discrepancy_count = (
        receipts.exclude(
            discrepancy_type=(
                ReceiptConfirmation
                .DiscrepancyType.NONE
            )
        ).count()
    )

    return {
        "role": User.Role.RECEIVER,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": {
            "requests_submitted": submitted,
            "pending_requests": pending,
            "approved_requests": approved,
            "donations_received": (
                completed_donations.count()
            ),
            "approval_rate": (
                calculate_percentage(
                    approved,
                    submitted,
                )
            ),
            "receipt_discrepancies": (
                discrepancy_count
            ),
        },
        "quantity_redistributed": (
            build_quantity_totals(receipts)
        ),
        "status_breakdown": (
            build_status_breakdown(requests)
        ),
        "monthly_trend": (
            build_monthly_trend(
                completed_donations
            )
        ),
    }


def get_volunteer_analytics(user):
    tasks = VolunteerTask.objects.filter(
        assigned_volunteer=user
    )

    assigned = tasks.count()

    completed = tasks.filter(
        status=VolunteerTask.Status.COMPLETED
    ).count()

    failed = tasks.filter(
        status=VolunteerTask.Status.FAILED
    ).count()

    cancelled = tasks.filter(
        status=VolunteerTask.Status.CANCELLED
    ).count()

    active = tasks.filter(
        status__in=[
            VolunteerTask.Status.ASSIGNED,
            VolunteerTask.Status.ARRIVED_AT_DONOR,
            VolunteerTask.Status.PICKED_UP,
            VolunteerTask.Status.ARRIVED_AT_RECEIVER,
            VolunteerTask.Status.DELIVERED,
        ]
    ).count()

    closed_tasks = (
        completed + failed + cancelled
    )

    transported_quantities = (
        tasks.filter(
            status=VolunteerTask.Status.COMPLETED
        )
        .values("unit")
        .annotate(
            total=Sum("required_quantity")
        )
        .order_by("unit")
    )

    quantities = [
        {
            "unit": row["unit"],
            "quantity": str(
                row["total"] or 0
            ),
        }
        for row in transported_quantities
    ]

    return {
        "role": User.Role.VOLUNTEER,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": {
            "tasks_assigned": assigned,
            "active_tasks": active,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "cancelled_tasks": cancelled,
            "task_completion_rate": (
                calculate_percentage(
                    completed,
                    closed_tasks,
                )
            ),
        },
        "quantity_redistributed": quantities,
        "status_breakdown": (
            build_status_breakdown(tasks)
        ),
        "monthly_trend": [],
    }


def get_admin_analytics():
    users = User.objects.all()
    donations = Donation.objects.all()

    total_donations = donations.count()

    completed = donations.filter(
        status=Donation.Status.COMPLETED
    ).count()

    unsuccessful = donations.filter(
        status__in=[
            Donation.Status.CANCELLED,
            Donation.Status.EXPIRED,
            Donation.Status.FAILED,
        ]
    ).count()

    eligible_outcomes = (
        completed + unsuccessful
    )

    receipts = (
        ReceiptConfirmation.objects
        .filter(
            donation__status=(
                Donation.Status.COMPLETED
            )
        )
    )

    user_role_rows = (
        users
        .values("role")
        .annotate(count=Count("id"))
        .order_by("role")
    )

    user_breakdown = [
        {
            "role": row["role"],
            "count": row["count"],
        }
        for row in user_role_rows
    ]

    open_complaints = (
        Complaint.objects.filter(
            status__in=[
                Complaint.Status.OPEN,
                Complaint.Status.IN_REVIEW,
            ]
        ).count()
    )

    recommendation_runs = 0

    if RecommendationRun is not None:
        recommendation_runs = (
            RecommendationRun.objects.count()
        )

    return {
        "role": User.Role.ADMIN,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": {
            "registered_users": (
                users.count()
            ),
            "active_users": (
                users.filter(
                    is_active=True
                ).count()
            ),
            "verified_participants": (
                users.filter(
                    verification_status=(
                        User.VerificationStatus
                        .VERIFIED
                    )
                ).count()
            ),
            "total_donations": (
                total_donations
            ),
            "completed_donations": completed,
            "unsuccessful_donations": (
                unsuccessful
            ),
            "completion_rate": (
                calculate_percentage(
                    completed,
                    eligible_outcomes,
                )
            ),
            "active_receivers": (
                ReceiverProfile.objects
                .filter(
                    operational=True,
                    user__is_active=True,
                )
                .count()
            ),
            "active_volunteers": (
                VolunteerProfile.objects
                .filter(
                    operational=True,
                    user__is_active=True,
                )
                .count()
            ),
            "open_complaints": (
                open_complaints
            ),
            "recommendation_runs": (
                recommendation_runs
            ),
        },
        "quantity_redistributed": (
            build_quantity_totals(receipts)
        ),
        "status_breakdown": (
            build_status_breakdown(
                donations
            )
        ),
        "user_breakdown": user_breakdown,
        "monthly_trend": (
            build_monthly_trend(
                donations
            )
        ),
    }


def get_analytics_for_user(user):
    if user.role == User.Role.DONOR:
        return get_donor_analytics(user)

    if user.role == User.Role.RECEIVER:
        return get_receiver_analytics(user)

    if user.role == User.Role.VOLUNTEER:
        return get_volunteer_analytics(user)

    if user.role == User.Role.ADMIN:
        return get_admin_analytics()

    return {
        "role": user.role,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": {},
        "quantity_redistributed": [],
        "status_breakdown": [],
        "monthly_trend": [],
    }