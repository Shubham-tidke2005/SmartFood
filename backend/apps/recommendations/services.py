from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
)
from apps.receivers.models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)

from .models import (
    RecommendationCandidate,
    RecommendationRun,
)


WEIGHTS = {
    "category_compatibility": 30,
    "capacity": 25,
    "distance": 20,
    "availability": 15,
    "successful_history": 10,
}


def normalize_area(value):
    return " ".join(
        (value or "").strip().lower().split()
    )


def calculate_distance_km(area_one, area_two):
    earth_radius = 6371.0088

    latitude_one = radians(
        float(area_one.latitude)
    )
    longitude_one = radians(
        float(area_one.longitude)
    )
    latitude_two = radians(
        float(area_two.latitude)
    )
    longitude_two = radians(
        float(area_two.longitude)
    )

    latitude_difference = (
        latitude_two - latitude_one
    )
    longitude_difference = (
        longitude_two - longitude_one
    )

    value = (
        sin(latitude_difference / 2) ** 2
        + cos(latitude_one)
        * cos(latitude_two)
        * sin(longitude_difference / 2) ** 2
    )

    return (
        2
        * earth_radius
        * asin(sqrt(value))
    )


def find_pickup_service_area(pickup_area):
    normalized_pickup_area = normalize_area(
        pickup_area
    )

    if not normalized_pickup_area:
        return None

    for service_area in ServiceArea.objects.filter(
        active=True
    ):
        possible_values = {
            normalize_area(service_area.code),
            normalize_area(service_area.name),
        }

        if normalized_pickup_area in possible_values:
            return service_area

    return None


def receiver_is_available(receiver, current_time=None):
    current_time = current_time or timezone.localtime()

    weekday = current_time.weekday()
    local_time = current_time.time()

    availability_windows = (
        ReceiverAvailability.objects.filter(
            receiver=receiver,
            active=True,
        )
    )

    for window in availability_windows:
        if window.starts_at <= window.ends_at:
            if (
                window.weekday == weekday
                and window.starts_at
                <= local_time
                <= window.ends_at
            ):
                return True
        else:
            if (
                window.weekday == weekday
                and local_time >= window.starts_at
            ):
                return True

            if (
                (window.weekday + 1) % 7
                == weekday
                and local_time <= window.ends_at
            ):
                return True

    return False


def receiver_has_allocation_capacity(
    receiver,
    profile,
):
    active_statuses = [
        Donation.Status.RESERVED,
        Donation.Status.PICKED_UP,
        Donation.Status.DELIVERED,
    ]

    active_allocation_count = (
        DonationRequest.objects.filter(
            receiver=receiver,
            status=DonationRequest.Status.APPROVED,
            donation__status__in=active_statuses,
        )
        .values("donation_id")
        .distinct()
        .count()
    )

    return (
        active_allocation_count
        < profile.max_active_allocations
    )


def get_receiver_requirement(
    receiver,
    revision,
):
    today = timezone.localdate()

    return (
        ReceiverRequirement.objects.filter(
            receiver=receiver,
            category=revision.category,
            unit=revision.unit,
            active=True,
        )
        .filter(
            Q(needed_until__isnull=True)
            | Q(needed_until__gte=today)
        )
        .order_by("needed_until")
        .first()
    )


def calculate_capacity_score(
    remaining_quantity,
    donation_quantity,
):
    if donation_quantity <= 0:
        return 0.0

    ratio = float(
        remaining_quantity / donation_quantity
    )

    normalized_ratio = min(ratio, 2.0) / 2.0

    return (
        normalized_ratio
        * WEIGHTS["capacity"]
    )


def calculate_distance_score(
    distance,
    maximum_distance,
):
    if distance is None:
        return 5.0

    maximum_distance = float(maximum_distance)

    if maximum_distance <= 0:
        return 0.0

    normalized_distance = min(
        distance / maximum_distance,
        1.0,
    )

    return (
        1.0 - normalized_distance
    ) * WEIGHTS["distance"]


def calculate_history_score(
    donation,
    receiver,
):
    successful_count = (
        DonationRequest.objects.filter(
            receiver=receiver,
            status=DonationRequest.Status.APPROVED,
            donation__donor=donation.donor,
            donation__status=Donation.Status.COMPLETED,
        )
        .values("donation_id")
        .distinct()
        .count()
    )

    normalized_count = min(
        successful_count,
        5,
    ) / 5

    score = (
        normalized_count
        * WEIGHTS["successful_history"]
    )

    return score, successful_count


def build_candidate(
    *,
    donation,
    revision,
    profile,
    pickup_service_area,
):
    receiver = profile.user

    category_accepted = (
        ReceiverPreference.objects.filter(
            receiver=receiver,
            category=revision.category,
            active=True,
        ).exists()
    )

    if not category_accepted:
        return None

    requirement = get_receiver_requirement(
        receiver,
        revision,
    )

    if requirement is None:
        return None

    remaining_quantity = (
        requirement.remaining_quantity
    )

    if remaining_quantity < revision.quantity:
        return None

    if not receiver_is_available(receiver):
        return None

    if not receiver_has_allocation_capacity(
        receiver,
        profile,
    ):
        return None

    approximate_distance = None

    if (
        pickup_service_area is not None
        and profile.service_area is not None
    ):
        approximate_distance = (
            calculate_distance_km(
                pickup_service_area,
                profile.service_area,
            )
        )

        if (
            approximate_distance
            > float(
                profile.max_service_distance_km
            )
        ):
            return None

    category_score = float(
        WEIGHTS["category_compatibility"]
    )

    capacity_score = calculate_capacity_score(
        remaining_quantity,
        revision.quantity,
    )

    availability_score = float(
        WEIGHTS["availability"]
    )

    distance_score = calculate_distance_score(
        approximate_distance,
        profile.max_service_distance_km,
    )

    history_score, successful_count = (
        calculate_history_score(
            donation,
            receiver,
        )
    )

    total_score = round(
        category_score
        + capacity_score
        + availability_score
        + distance_score
        + history_score,
        2,
    )

    explanations = [
        (
            f"Accepts the "
            f"{revision.category.name} category."
        ),
        (
            f"Has {remaining_quantity} "
            f"{revision.unit} remaining capacity."
        ),
        "Currently available to receive food.",
    ]

    if approximate_distance is None:
        explanations.append(
            "Approximate distance could not be "
            "calculated from the available area data."
        )
    else:
        explanations.append(
            f"Approximately "
            f"{approximate_distance:.2f} km away "
            f"by straight-line distance."
        )

    if successful_count > 0:
        explanations.append(
            f"{successful_count} previous successful "
            f"interaction(s) with this donor."
        )
    else:
        explanations.append(
            "No previous completed interaction with "
            "this donor."
        )

    organization_name = (
        profile.organization_name
        or receiver.display_name
    )

    return {
        "receiver": receiver,
        "score": total_score,
        "distance": approximate_distance,
        "remaining_capacity": remaining_quantity,
        "feature_snapshot": {
            "receiver_id": str(receiver.id),
            "organization_name": organization_name,
            "category_compatible": True,
            "category_score": round(
                category_score,
                2,
            ),
            "capacity_score": round(
                capacity_score,
                2,
            ),
            "availability_score": round(
                availability_score,
                2,
            ),
            "distance_score": round(
                distance_score,
                2,
            ),
            "history_score": round(
                history_score,
                2,
            ),
            "successful_interactions": (
                successful_count
            ),
            "unit": revision.unit,
            "donation_quantity": str(
                revision.quantity
            ),
            "remaining_capacity": str(
                remaining_quantity
            ),
        },
        "explanations": explanations,
    }


@transaction.atomic
def generate_recommendations(
    *,
    donation,
    requested_by,
):
    locked_donation = (
        Donation.objects
        .select_for_update()
        .select_related("donor")
        .get(pk=donation.pk)
    )

    if (
        locked_donation.status
        != Donation.Status.AVAILABLE
    ):
        raise ValueError(
            "Recommendations can only be generated "
            "for an available donation."
        )

    revision = (
        locked_donation.revisions
        .select_related("category")
        .filter(is_current=True)
        .first()
    )

    if revision is None:
        raise ValueError(
            "The donation has no current revision."
        )

    if revision.pickup_deadline <= timezone.now():
        raise ValueError(
            "Recommendations cannot be generated "
            "after the pickup deadline."
        )

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
        .filter(
            operational=True,
            user__role=User.Role.RECEIVER,
            user__is_active=True,
            user__contact_verified_at__isnull=False,
            user__verification_status=(
                User.VerificationStatus.VERIFIED
            ),
            service_area__active=True,
        )
    )

    scored_candidates = []

    for profile in profiles:
        candidate = build_candidate(
            donation=locked_donation,
            revision=revision,
            profile=profile,
            pickup_service_area=(
                pickup_service_area
            ),
        )

        if candidate is not None:
            scored_candidates.append(candidate)

    scored_candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    run = RecommendationRun.objects.create(
        donation=locked_donation,
        revision=revision,
        requested_by=requested_by,
        algorithm=(
            RecommendationRun.Algorithm
            .RULE_BASED_V1
        ),
        model_version="baseline-1.0",
        status=RecommendationRun.Status.COMPLETED,
        weights=WEIGHTS,
        candidate_count=len(scored_candidates),
    )

    candidate_records = []

    for index, candidate in enumerate(
        scored_candidates,
        start=1,
    ):
        distance = candidate["distance"]

        candidate_records.append(
            RecommendationCandidate(
                run=run,
                receiver=candidate["receiver"],
                rank=index,
                score=Decimal(
                    str(candidate["score"])
                ),
                approximate_distance_km=(
                    Decimal(
                        str(round(distance, 2))
                    )
                    if distance is not None
                    else None
                ),
                remaining_capacity=(
                    candidate[
                        "remaining_capacity"
                    ]
                ),
                feature_snapshot=(
                    candidate["feature_snapshot"]
                ),
                explanations=(
                    candidate["explanations"]
                ),
            )
        )

    RecommendationCandidate.objects.bulk_create(
        candidate_records
    )

    return (
        RecommendationRun.objects
        .prefetch_related("candidates__receiver")
        .get(pk=run.pk)
    )