from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.receivers.models import (
    ReceiverAvailability,
    ReceiverProfile,
)

from .eligibility import (
    evaluate_receiver_eligibility,
    find_pickup_service_area,
)


ZERO = Decimal("0")
ONE = Decimal("1")


def clamp(value, minimum=ZERO, maximum=ONE):
    value = Decimal(str(value))

    return max(
        minimum,
        min(value, maximum),
    )


def get_all_candidate_decisions(
    *,
    donation,
    revision,
):
    """
    Evaluate every receiver profile.

    The returned list includes eligible and rejected
    receivers so RecommendationEvaluation can preserve
    every candidate considered.
    """
    pickup_service_area = (
        find_pickup_service_area(
            revision.pickup_area
        )
    )

    profiles = (
        ReceiverProfile.objects
        .select_related(
            "user",
            "service_area",
        )
        .order_by(
            "organization_name",
            "user_id",
        )
    )

    return [
        evaluate_receiver_eligibility(
            profile=profile,
            donation=donation,
            revision=revision,
            pickup_service_area=(
                pickup_service_area
            ),
        )
        for profile in profiles
    ]


def build_local_datetime(
    date_value,
    time_value,
):
    combined = datetime.combine(
        date_value,
        time_value,
    )

    return timezone.make_aware(
        combined,
        timezone.get_current_timezone(),
    )


def get_window_intersection(
    interval_start,
    interval_end,
    pickup_start,
    pickup_end,
):
    start = max(
        interval_start,
        pickup_start,
    )

    end = min(
        interval_end,
        pickup_end,
    )

    if end <= start:
        return None

    return start, end


def merge_intervals(intervals):
    if not intervals:
        return []

    ordered = sorted(
        intervals,
        key=lambda interval: interval[0],
    )

    merged = [ordered[0]]

    for current_start, current_end in ordered[1:]:
        last_start, last_end = merged[-1]

        if current_start <= last_end:
            merged[-1] = (
                last_start,
                max(last_end, current_end),
            )
        else:
            merged.append(
                (current_start, current_end)
            )

    return merged


def calculate_availability_overlap(
    *,
    receiver,
    pickup_starts_at,
    pickup_deadline,
):
    """
    Return how much of the donation pickup interval overlaps
    the receiver's active availability.

    The result is normalized between 0 and 1.
    """
    local_start = timezone.localtime(
        pickup_starts_at
    )
    local_end = timezone.localtime(
        pickup_deadline
    )

    total_seconds = (
        local_end - local_start
    ).total_seconds()

    if total_seconds <= 0:
        return ZERO

    availability_windows = list(
        ReceiverAvailability.objects.filter(
            receiver=receiver,
            active=True,
        )
    )

    intersections = []

    current_date = local_start.date()
    final_date = local_end.date()

    while current_date <= final_date:
        for window in availability_windows:
            if (
                window.weekday
                != current_date.weekday()
            ):
                continue

            interval_start = (
                build_local_datetime(
                    current_date,
                    window.starts_at,
                )
            )

            if (
                window.starts_at
                < window.ends_at
            ):
                interval_end = (
                    build_local_datetime(
                        current_date,
                        window.ends_at,
                    )
                )
            elif (
                window.starts_at
                > window.ends_at
            ):
                interval_end = (
                    build_local_datetime(
                        current_date
                        + timedelta(days=1),
                        window.ends_at,
                    )
                )
            else:
                continue

            intersection = (
                get_window_intersection(
                    interval_start,
                    interval_end,
                    local_start,
                    local_end,
                )
            )

            if intersection:
                intersections.append(
                    intersection
                )

        current_date += timedelta(days=1)

    merged_intervals = merge_intervals(
        intersections
    )

    overlap_seconds = sum(
        (
            interval_end
            - interval_start
        ).total_seconds()
        for interval_start, interval_end
        in merged_intervals
    )

    return clamp(
        Decimal(str(
            overlap_seconds / total_seconds
        ))
    )


def calculate_distance_feature(
    *,
    approximate_distance_km,
    maximum_distance_km,
):
    """
    1.0 means very near.
    0.0 means at or beyond the allowed maximum distance.
    """
    if approximate_distance_km is None:
        return ZERO

    maximum_distance = Decimal(
        str(maximum_distance_km)
    )

    if maximum_distance <= 0:
        return ZERO

    distance = Decimal(
        str(approximate_distance_km)
    )

    return clamp(
        ONE - (
            distance / maximum_distance
        )
    )


def calculate_quantity_match_feature(
    *,
    donation_quantity,
    remaining_quantity,
):
    """
    Measures how much of the receiver's remaining need
    is satisfied by this donation.

    Example:
    donation=25, remaining need=100 -> 0.25
    donation=25, remaining need=25  -> 1.00

    Eligibility already guarantees that the receiver has
    enough remaining capacity.
    """
    donation_quantity = Decimal(
        str(donation_quantity)
    )

    remaining_quantity = Decimal(
        str(remaining_quantity)
    )

    if (
        donation_quantity <= 0
        or remaining_quantity <= 0
    ):
        return ZERO

    return clamp(
        donation_quantity
        / remaining_quantity
    )


def calculate_transport_readiness_feature(
    *,
    active_allocations,
    maximum_allocations,
    collection_feasible,
):
    """
    Transport readiness uses remaining operational task
    capacity.

    A receiver with no active allocations receives 1.0.
    A receiver close to its limit receives a lower score.
    """
    if not collection_feasible:
        return ZERO

    maximum_allocations = int(
        maximum_allocations
    )

    if maximum_allocations <= 0:
        return ZERO

    active_allocations = max(
        int(active_allocations),
        0,
    )

    readiness = (
        Decimal(
            maximum_allocations
            - active_allocations
        )
        / Decimal(maximum_allocations)
    )

    return clamp(readiness)


def build_considered_feature_snapshot(
    *,
    decision,
    revision,
):
    requirement = decision.requirement

    remaining_capacity = None

    if requirement is not None:
        remaining_capacity = str(
            requirement.remaining_quantity
        )

    return {
        "category_id": str(
            revision.category_id
        ),
        "category_name": (
            revision.category.name
        ),
        "donation_quantity": str(
            revision.quantity
        ),
        "unit": revision.unit,
        "pickup_starts_at": (
            revision.pickup_starts_at.isoformat()
        ),
        "pickup_deadline": (
            revision.pickup_deadline.isoformat()
        ),
        "pickup_area": (
            revision.pickup_area
        ),
        "remaining_capacity": (
            remaining_capacity
        ),
        "approximate_distance_km": (
            str(
                decision
                .approximate_distance_km
            )
            if (
                decision
                .approximate_distance_km
                is not None
            )
            else None
        ),
        "maximum_service_distance_km": str(
            decision
            .profile
            .max_service_distance_km
        ),
        "maximum_active_allocations": (
            decision
            .profile
            .max_active_allocations
        ),
    }


def build_baseline_features(
    *,
    decision,
    revision,
):
    if not decision.eligible:
        raise ValueError(
            "Baseline features can only be generated "
            "for an eligible receiver."
        )

    requirement = decision.requirement
    profile = decision.profile
    receiver = profile.user

    from .eligibility import (
        count_active_allocations,
    )

    active_allocations = (
        count_active_allocations(receiver)
    )

    normalized_features = {
        "distance": (
            calculate_distance_feature(
                approximate_distance_km=(
                    decision
                    .approximate_distance_km
                ),
                maximum_distance_km=(
                    profile
                    .max_service_distance_km
                ),
            )
        ),
        "quantity_match": (
            calculate_quantity_match_feature(
                donation_quantity=(
                    revision.quantity
                ),
                remaining_quantity=(
                    requirement
                    .remaining_quantity
                ),
            )
        ),
        "availability_overlap": (
            calculate_availability_overlap(
                receiver=receiver,
                pickup_starts_at=(
                    revision
                    .pickup_starts_at
                ),
                pickup_deadline=(
                    revision
                    .pickup_deadline
                ),
            )
        ),
        "transport_readiness": (
            calculate_transport_readiness_feature(
                active_allocations=(
                    active_allocations
                ),
                maximum_allocations=(
                    profile
                    .max_active_allocations
                ),
                collection_feasible=(
                    decision.checks.get(
                        "collection_feasible",
                        False,
                    )
                ),
            )
        ),
    }

    snapshot = (
        build_considered_feature_snapshot(
            decision=decision,
            revision=revision,
        )
    )

    snapshot.update({
        "active_allocations": (
            active_allocations
        ),
        "eligibility_checks": (
            decision.checks
        ),
        "normalized_features": {
            name: round(
                float(value),
                6,
            )
            for name, value
            in normalized_features.items()
        },
    })

    return normalized_features, snapshot