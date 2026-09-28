from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.db.models import Q
from django.utils import timezone
from django.db import transaction


from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
)
from apps.receivers.models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    profile: ReceiverProfile | None
    requirement: ReceiverRequirement | None
    approximate_distance_km: Decimal | None
    rejection_reasons: tuple[str, ...]
    checks: dict
    

def normalize_area(value):
    return " ".join(
        (value or "").strip().lower().split()
    )


def calculate_distance_km(area_one, area_two):
    """
    Calculate approximate straight-line distance.

    This value must not be presented as road distance
    or driving time.
    """
    earth_radius_km = 6371.0088

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

    haversine_value = (
        sin(latitude_difference / 2) ** 2
        + cos(latitude_one)
        * cos(latitude_two)
        * sin(longitude_difference / 2) ** 2
    )

    distance = (
        2
        * earth_radius_km
        * asin(sqrt(haversine_value))
    )

    return Decimal(str(round(distance, 2)))


def find_pickup_service_area(pickup_area):
    """
    Match DonationRevision.pickup_area with a controlled
    ServiceArea code or name.

    The function deliberately uses exact normalized matching.
    Fuzzy matching could silently select the wrong location.
    """
    normalized_pickup_area = normalize_area(
        pickup_area
    )

    if not normalized_pickup_area:
        return None

    service_areas = ServiceArea.objects.filter(
        active=True
    )

    for service_area in service_areas:
        possible_values = {
            normalize_area(service_area.code),
            normalize_area(service_area.name),
        }

        if normalized_pickup_area in possible_values:
            return service_area

    return None


def build_local_datetime(date_value, time_value):
    current_timezone = (
        timezone.get_current_timezone()
    )

    combined = datetime.combine(
        date_value,
        time_value,
    )

    return timezone.make_aware(
        combined,
        current_timezone,
    )


def availability_window_overlaps(
    availability,
    pickup_starts_at,
    pickup_deadline,
):
    """
    Check whether one weekly receiver availability window
    overlaps the donation pickup interval.

    Overnight availability is supported. For example:
    Saturday 22:00 to 02:00 means Saturday night through
    Sunday morning.
    """
    local_pickup_start = timezone.localtime(
        pickup_starts_at
    )
    local_pickup_deadline = timezone.localtime(
        pickup_deadline
    )

    current_date = local_pickup_start.date()
    final_date = local_pickup_deadline.date()

    while current_date <= final_date:
        if (
            current_date.weekday()
            == availability.weekday
        ):
            window_start = build_local_datetime(
                current_date,
                availability.starts_at,
            )

            if (
                availability.starts_at
                < availability.ends_at
            ):
                window_end = build_local_datetime(
                    current_date,
                    availability.ends_at,
                )
            elif (
                availability.starts_at
                > availability.ends_at
            ):
                window_end = build_local_datetime(
                    current_date
                    + timedelta(days=1),
                    availability.ends_at,
                )
            else:
                # Equal start and end is treated as an
                # invalid zero-length availability window.
                current_date += timedelta(days=1)
                continue

            if (
                window_start
                <= local_pickup_deadline
                and window_end
                >= local_pickup_start
            ):
                return True

        current_date += timedelta(days=1)

    return False


def receiver_is_available(
    receiver,
    revision,
):
    """
    A receiver is available when at least one active
    receiving window overlaps the donation pickup window.
    """
    availability_windows = (
        ReceiverAvailability.objects.filter(
            receiver=receiver,
            active=True,
        )
    )

    return any(
        availability_window_overlaps(
            availability,
            revision.pickup_starts_at,
            revision.pickup_deadline,
        )
        for availability in availability_windows
    )


def get_receiver_requirement(
    receiver,
    revision,
    *,
    lock=False,
):
    pickup_date = timezone.localtime(
        revision.pickup_deadline
    ).date()

    queryset = (
        ReceiverRequirement.objects.filter(
            receiver=receiver,
            category=revision.category,
            unit=revision.unit,
            active=True,
        )
        .filter(
            Q(needed_until__isnull=True)
            | Q(needed_until__gte=pickup_date)
        )
        .order_by(
            "needed_until",
            "created_at",
        )
    )

    if lock:
        queryset = (
            queryset.select_for_update()
        )

    return queryset.first()


def count_active_allocations(receiver):
    active_statuses = [
        Donation.Status.RESERVED,
        Donation.Status.PICKED_UP,
        Donation.Status.DELIVERED,
    ]

    return (
        DonationRequest.objects.filter(
            receiver=receiver,
            status=(
                DonationRequest.Status.APPROVED
            ),
            donation__status__in=active_statuses,
        )
        .values("donation_id")
        .distinct()
        .count()
    )


def receiver_has_allocation_capacity(
    receiver,
    profile,
):
    active_allocation_count = (
        count_active_allocations(receiver)
    )

    return (
        active_allocation_count
        < profile.max_active_allocations
    )


def evaluate_receiver_eligibility(
    *,
    profile,
    donation,
    revision,
    pickup_service_area=None,
    lock_requirement=False,
):
    """
    Apply all hard eligibility rules to one receiver.

    Recommendation scoring and ML must only run when this
    function returns an eligible decision.
    """
    receiver = profile.user

    rejection_reasons = []

    checks = {
        "correct_role": False,
        "account_active": False,
        "contact_verified": False,
        "participant_verified": False,
        "profile_operational": False,
        "food_compatible": False,
        "handling_capable": False,
        "capacity_available": False,
        "receiving_available": False,
        "service_area_active": False,
        "service_area_resolved": False,
        "within_service_distance": False,
        "allocation_slot_available": False,
        "collection_feasible": False,
    }

    requirement = None
    approximate_distance = None

    checks["correct_role"] = (
        receiver.role == User.Role.RECEIVER
    )

    if not checks["correct_role"]:
        rejection_reasons.append(
            "Receiver account has an invalid role."
        )

    checks["account_active"] = receiver.is_active

    if not checks["account_active"]:
        rejection_reasons.append(
            "Receiver account is inactive."
        )

    checks["contact_verified"] = (
        receiver.contact_verified_at is not None
    )

    if not checks["contact_verified"]:
        rejection_reasons.append(
            "Receiver contact is not verified."
        )

    checks["participant_verified"] = (
        receiver.verification_status
        == User.VerificationStatus.VERIFIED
    )

    if not checks["participant_verified"]:
        rejection_reasons.append(
            "Receiver participant verification is incomplete."
        )

    checks["profile_operational"] = (
        profile.operational
    )

    if not checks["profile_operational"]:
        rejection_reasons.append(
            "Receiver organization is not operational."
        )

    checks["service_area_active"] = bool(
        profile.service_area_id
        and profile.service_area.active
    )

    if not checks["service_area_active"]:
        rejection_reasons.append(
            "Receiver service area is inactive."
        )

    checks["food_compatible"] = (
        ReceiverPreference.objects.filter(
            receiver=receiver,
            category=revision.category,
            active=True,
        ).exists()
    )

    if not checks["food_compatible"]:
        rejection_reasons.append(
            "Receiver does not accept this food category."
        )

    requirement = get_receiver_requirement(
        receiver,
        revision,
        lock=lock_requirement,
    )

    checks["handling_capable"] = (
        checks["food_compatible"]
        and requirement is not None
    )

    if requirement is None:
        rejection_reasons.append(
            "Receiver has no active requirement for this "
            "food category and unit."
        )
    else:
        checks["capacity_available"] = (
            requirement.remaining_quantity
            >= revision.quantity
        )

        if not checks["capacity_available"]:
            rejection_reasons.append(
                "Receiver does not have enough remaining "
                "quantity capacity."
            )

    checks["receiving_available"] = (
        receiver_is_available(
            receiver,
            revision,
        )
    )

    if not checks["receiving_available"]:
        rejection_reasons.append(
            "Receiver is unavailable during the pickup window."
        )

    checks["allocation_slot_available"] = (
        receiver_has_allocation_capacity(
            receiver,
            profile,
        )
    )

    if not checks["allocation_slot_available"]:
        rejection_reasons.append(
            "Receiver has reached its active allocation limit."
        )

    checks["service_area_resolved"] = (
        pickup_service_area is not None
    )

    if pickup_service_area is None:
        rejection_reasons.append(
            "Donation pickup area does not match an active "
            "configured service area."
        )
    elif checks["service_area_active"]:
        approximate_distance = (
            calculate_distance_km(
                pickup_service_area,
                profile.service_area,
            )
        )

        checks["within_service_distance"] = (
            approximate_distance
            <= profile.max_service_distance_km
        )

        if not checks["within_service_distance"]:
            rejection_reasons.append(
                "Donation is outside the receiver's "
                "maximum service distance."
            )

    checks["collection_feasible"] = all(
        [
            checks["receiving_available"],
            checks["service_area_active"],
            checks["service_area_resolved"],
            checks["within_service_distance"],
            checks["allocation_slot_available"],
        ]
    )

    if (
        not checks["collection_feasible"]
        and not any(
            reason.startswith(
                "Receiver is unavailable"
            )
            or reason.startswith(
                "Receiver service area"
            )
            or reason.startswith(
                "Donation pickup area"
            )
            or reason.startswith(
                "Donation is outside"
            )
            or reason.startswith(
                "Receiver has reached"
            )
            for reason in rejection_reasons
        )
    ):
        rejection_reasons.append(
            "Collection is not operationally feasible."
        )

    eligible = all(
        [
            checks["correct_role"],
            checks["account_active"],
            checks["contact_verified"],
            checks["participant_verified"],
            checks["profile_operational"],
            checks["food_compatible"],
            checks["handling_capable"],
            checks["capacity_available"],
            checks["receiving_available"],
            checks["service_area_active"],
            checks["service_area_resolved"],
            checks["within_service_distance"],
            checks["allocation_slot_available"],
            checks["collection_feasible"],
        ]
    )

    return EligibilityDecision(
        eligible=eligible,
        profile=profile,
        requirement=requirement,
        approximate_distance_km=(
            approximate_distance
        ),
        rejection_reasons=tuple(
            rejection_reasons
        ),
        checks=checks,
    )


def get_eligible_candidates(
    *,
    donation,
    revision,
):
    """
    Return only receivers that pass every hard eligibility
    rule.

    Both the rule-based baseline and future ML model must
    consume this function.
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
        .filter(
            user__role=User.Role.RECEIVER,
        )
        .order_by(
            "organization_name"
        )
    )

    eligible_candidates = []

    for profile in profiles:
        decision = evaluate_receiver_eligibility(
            profile=profile,
            donation=donation,
            revision=revision,
            pickup_service_area=(
                pickup_service_area
            ),
        )

        if decision.eligible:
            eligible_candidates.append(
                decision
            )

    return eligible_candidates


def recheck_receiver_eligibility(
    *,
    receiver,
    donation,
    revision,
    lock=False,
):
    """
    Recheck live eligibility when a request is submitted
    or approved.

    With lock=True, the receiver account, profile and
    matching requirement are protected until the surrounding
    transaction finishes.
    """
    if (
        lock
        and not transaction
        .get_connection()
        .in_atomic_block
    ):
        raise RuntimeError(
            "Eligibility locking requires an active "
            "database transaction."
        )

    receiver_queryset = User.objects.all()

    if lock:
        receiver_queryset = (
            receiver_queryset.select_for_update()
        )

    current_receiver = (
        receiver_queryset.get(pk=receiver.pk)
    )

    profile_queryset = (
        ReceiverProfile.objects.select_related(
            "service_area"
        )
    )

    if lock:
        profile_queryset = (
            profile_queryset.select_for_update()
        )

    try:
        profile = profile_queryset.get(
            user=current_receiver
        )
    except ReceiverProfile.DoesNotExist:
        return EligibilityDecision(
            eligible=False,
            profile=None,
            requirement=None,
            approximate_distance_km=None,
            rejection_reasons=(
                "Receiver profile does not exist.",
            ),
            checks={
                "receiver_profile_exists": False,
            },
        )

    pickup_service_area = (
        find_pickup_service_area(
            revision.pickup_area
        )
    )

    return evaluate_receiver_eligibility(
        profile=profile,
        donation=donation,
        revision=revision,
        pickup_service_area=(
            pickup_service_area
        ),
        lock_requirement=lock,
    )