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
    HandoverRecord,
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


ACTIVE_DONATION_STATUSES = [
    Donation.Status.AVAILABLE,
    Donation.Status.RESERVED,
    Donation.Status.PICKED_UP,
    Donation.Status.DELIVERED,
]

PENDING_COLLECTION_STATUSES = [
    Donation.Status.RESERVED,
    Donation.Status.PICKED_UP,
    Donation.Status.DELIVERED,
]

ACTIVE_TASK_STATUSES = [
    VolunteerTask.Status.ASSIGNED,
    VolunteerTask.Status.ARRIVED_AT_DONOR,
    VolunteerTask.Status.PICKED_UP,
    VolunteerTask.Status.ARRIVED_AT_RECEIVER,
    VolunteerTask.Status.DELIVERED,
]


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


def average_elapsed_hours(
    rows,
    start_key,
    end_key,
):
    durations = []

    for row in rows:
        started_at = row.get(start_key)
        ended_at = row.get(end_key)

        if not started_at or not ended_at:
            continue

        if ended_at < started_at:
            continue

        durations.append(
            (
                ended_at - started_at
            ).total_seconds()
        )

    if not durations:
        return 0.0

    average_seconds = (
        sum(durations) / len(durations)
    )

    return round(
        average_seconds / 3600,
        2,
    )


def previous_month(
    month,
    difference,
):
    month_index = (
        month.year * 12
        + month.month
        - 1
        - difference
    )

    return month.replace(
        year=month_index // 12,
        month=month_index % 12 + 1,
        day=1,
    )


def get_month_values(months=6):
    current_month = (
        timezone.localdate()
        .replace(day=1)
    )

    return [
        previous_month(
            current_month,
            difference,
        )
        for difference in reversed(
            range(months)
        )
    ]


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
    """
    Sum actual receiver-confirmed accepted quantities.

    Quantities remain separated by unit. Kilograms,
    litres, portions and packages are never combined.
    """
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


def build_quantity_trend(
    receipts,
    months=6,
):
    """
    Build monthly redistribution totals while preserving
    each unit as an independent measurement.
    """
    month_values = get_month_values(
        months
    )
    start_date = month_values[0]

    rows = (
        receipts
        .filter(
            received_at__date__gte=start_date
        )
        .annotate(
            month=TruncMonth("received_at")
        )
        .values(
            "month",
            "unit",
        )
        .annotate(
            total=Sum("accepted_quantity")
        )
        .order_by(
            "month",
            "unit",
        )
    )

    totals = defaultdict(dict)

    for row in rows:
        month_key = row[
            "month"
        ].strftime("%Y-%m")

        totals[month_key][
            row["unit"]
        ] = str(
            row["total"] or 0
        )

    return [
        {
            "month": month.strftime(
                "%Y-%m"
            ),
            "label": month.strftime(
                "%b %Y"
            ),
            "quantities": [
                {
                    "unit": unit,
                    "quantity": quantity,
                }
                for unit, quantity in sorted(
                    totals.get(
                        month.strftime("%Y-%m"),
                        {},
                    ).items()
                )
            ],
        }
        for month in month_values
    ]


def build_monthly_trend(
    donation_queryset,
    months=6,
):
    month_values = get_month_values(
        months
    )
    start_date = month_values[0]

    created_rows = (
        donation_queryset
        .filter(
            created_at__date__gte=start_date
        )
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

    created_map = {
        row["month"].strftime("%Y-%m"): (
            row["count"]
        )
        for row in created_rows
    }

    completed_map = {
        row["month"].strftime("%Y-%m"): (
            row["count"]
        )
        for row in completed_rows
    }

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


def build_base_response(
    *,
    role,
    summary,
    receipts,
    status_breakdown,
    monthly_trend,
):
    return {
        "role": role,
        "generated_at": (
            timezone.now().isoformat()
        ),
        "summary": summary,
        "quantity_redistributed": (
            build_quantity_totals(
                receipts
            )
        ),
        "quantity_trend": (
            build_quantity_trend(
                receipts
            )
        ),
        "status_breakdown": (
            status_breakdown
        ),
        "monthly_trend": monthly_trend,
    }


def get_donor_analytics(user):
    donations = Donation.objects.filter(
        donor=user
    )

    completed = donations.filter(
        status=Donation.Status.COMPLETED
    ).count()

    cancelled = donations.filter(
        status=Donation.Status.CANCELLED
    ).count()

    expired = donations.filter(
        status=Donation.Status.EXPIRED
    ).count()

    failed = donations.filter(
        status=Donation.Status.FAILED
    ).count()

    closed = (
        completed
        + cancelled
        + expired
        + failed
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

    summary = {
        "listings_created": (
            donations.count()
        ),
        # Kept for older frontend compatibility.
        "donations_created": (
            donations.count()
        ),
        "active_donations": (
            donations.filter(
                status__in=(
                    ACTIVE_DONATION_STATUSES
                )
            ).count()
        ),
        "completed_donations": completed,
        "cancelled_donations": cancelled,
        "expired_donations": expired,
        "failed_donations": failed,
        "completion_rate": (
            calculate_percentage(
                completed,
                closed,
            )
        ),
        "receipt_discrepancies": (
            receipts.exclude(
                discrepancy_type=(
                    ReceiptConfirmation
                    .DiscrepancyType.NONE
                )
            ).count()
        ),
    }

    return build_base_response(
        role=User.Role.DONOR,
        summary=summary,
        receipts=receipts,
        status_breakdown=(
            build_status_breakdown(
                donations
            )
        ),
        monthly_trend=(
            build_monthly_trend(
                donations
            )
        ),
    )


def get_receiver_analytics(user):
    requests = (
        DonationRequest.objects
        .filter(receiver=user)
    )

    approved_requests = (
        requests.filter(
            status=(
                DonationRequest.Status.APPROVED
            )
        )
    )

    completed_donations = (
        Donation.objects
        .filter(
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

    submitted = requests.count()
    approved = approved_requests.count()

    summary = {
        "requests_submitted": submitted,
        "pending_requests": (
            requests.filter(
                status=(
                    DonationRequest.Status.PENDING
                )
            ).count()
        ),
        "approved_donations": approved,
        # Kept for older frontend compatibility.
        "approved_requests": approved,
        "donations_received": (
            receipts.count()
        ),
        "pending_collections": (
            approved_requests.filter(
                donation__status__in=(
                    PENDING_COLLECTION_STATUSES
                )
            ).count()
        ),
        "approval_rate": (
            calculate_percentage(
                approved,
                submitted,
            )
        ),
        "receipt_discrepancies": (
            receipts.exclude(
                discrepancy_type=(
                    ReceiptConfirmation
                    .DiscrepancyType.NONE
                )
            ).count()
        ),
    }

    return build_base_response(
        role=User.Role.RECEIVER,
        summary=summary,
        receipts=receipts,
        status_breakdown=(
            build_status_breakdown(
                requests
            )
        ),
        monthly_trend=(
            build_monthly_trend(
                completed_donations
            )
        ),
    )


def get_volunteer_analytics(user):
    tasks = (
        VolunteerTask.objects
        .filter(
            assigned_volunteer=user
        )
    )

    accepted = tasks.filter(
        assigned_at__isnull=False
    ).count()

    completed = tasks.filter(
        status=VolunteerTask.Status.COMPLETED
    ).count()

    failed = tasks.filter(
        status=VolunteerTask.Status.FAILED
    ).count()

    cancelled = tasks.filter(
        status=VolunteerTask.Status.CANCELLED
    ).count()

    closed = (
        completed
        + failed
        + cancelled
    )

    receipts = (
        ReceiptConfirmation.objects
        .filter(
            donation__volunteer_task__assigned_volunteer=(
                user
            ),
            donation__status=(
                Donation.Status.COMPLETED
            ),
        )
    )

    summary = {
        "tasks_accepted": accepted,
        # Kept for older frontend compatibility.
        "tasks_assigned": accepted,
        "active_tasks": (
            tasks.filter(
                status__in=(
                    ACTIVE_TASK_STATUSES
                )
            ).count()
        ),
        "deliveries_recorded": (
            tasks.filter(
                delivered_at__isnull=False
            ).count()
        ),
        "completed_tasks": completed,
        "failed_tasks": failed,
        "cancelled_tasks": cancelled,
        "task_completion_rate": (
            calculate_percentage(
                completed,
                closed,
            )
        ),
    }

    return build_base_response(
        role=User.Role.VOLUNTEER,
        summary=summary,
        receipts=receipts,
        status_breakdown=(
            build_status_breakdown(
                tasks
            )
        ),
        monthly_trend=[],
    )


def get_admin_analytics():
    users = User.objects.all()

    participants = users.exclude(
        role=User.Role.ADMIN
    )

    donations = Donation.objects.all()

    completed = donations.filter(
        status=Donation.Status.COMPLETED
    ).count()

    cancelled = donations.filter(
        status=Donation.Status.CANCELLED
    ).count()

    expired = donations.filter(
        status=Donation.Status.EXPIRED
    ).count()

    failed = donations.filter(
        status=Donation.Status.FAILED
    ).count()

    closed = (
        completed
        + cancelled
        + expired
        + failed
    )

    receipts = (
        ReceiptConfirmation.objects
        .filter(
            donation__status=(
                Donation.Status.COMPLETED
            )
        )
    )

    approved_rows = list(
        DonationRequest.objects
        .filter(
            status=(
                DonationRequest.Status.APPROVED
            ),
            decided_at__isnull=False,
        )
        .values(
            "created_at",
            "decided_at",
        )
    )

    pickup_rows = list(
        HandoverRecord.objects
        .filter(
            donation_request__decided_at__isnull=False,
            handed_over_at__isnull=False,
        )
        .values(
            "donation_request__decided_at",
            "handed_over_at",
        )
    )

    average_approval_hours = (
        average_elapsed_hours(
            approved_rows,
            "created_at",
            "decided_at",
        )
    )

    average_pickup_hours = (
        average_elapsed_hours(
            pickup_rows,
            "donation_request__decided_at",
            "handed_over_at",
        )
    )

    open_complaints = (
        Complaint.objects
        .filter(
            status__in=[
                Complaint.Status.OPEN,
                Complaint.Status.IN_REVIEW,
            ]
        )
        .count()
    )

    total_complaints = (
        Complaint.objects.count()
    )

    if RecommendationRun is None:
        recommendation_runs = 0
    else:
        recommendation_runs = (
            RecommendationRun.objects.count()
        )

    user_breakdown = list(
        users
        .values("role")
        .annotate(count=Count("id"))
        .order_by("role")
    )

    summary = {
        "registered_users": users.count(),
        "active_users": (
            users.filter(
                is_active=True
            ).count()
        ),
        "active_participants": (
            participants.filter(
                is_active=True
            ).count()
        ),
        "verified_participants": (
            participants.filter(
                verification_status=(
                    User.VerificationStatus.VERIFIED
                ),
                is_active=True,
            ).count()
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
        "total_donations": (
            donations.count()
        ),
        "completed_donations": completed,
        "cancelled_donations": cancelled,
        "expired_donations": expired,
        "failed_donations": failed,
        "completion_rate": (
            calculate_percentage(
                completed,
                closed,
            )
        ),
        "average_approval_hours": (
            average_approval_hours
        ),
        "average_pickup_hours": (
            average_pickup_hours
        ),
        "total_complaints": (
            total_complaints
        ),
        "open_complaints": (
            open_complaints
        ),
        "closed_complaints": (
            total_complaints
            - open_complaints
        ),
        "recommendation_runs": (
            recommendation_runs
        ),
    }

    response = build_base_response(
        role=User.Role.ADMIN,
        summary=summary,
        receipts=receipts,
        status_breakdown=(
            build_status_breakdown(
                donations
            )
        ),
        monthly_trend=(
            build_monthly_trend(
                donations
            )
        ),
    )

    response["user_breakdown"] = (
        user_breakdown
    )

    response["operational_timings"] = {
        "average_approval_hours": (
            average_approval_hours
        ),
        "average_pickup_hours": (
            average_pickup_hours
        ),
    }

    return response


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
        "quantity_trend": [],
        "status_breakdown": [],
        "monthly_trend": [],
    }