from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVerifiedReceiver
from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
)

from .models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)
from .serializers import (
    ReceiverAvailabilitySerializer,
    ReceiverDiscoveryFilterSerializer,
    ReceiverPreferenceSerializer,
    ReceiverProfileSerializer,
    ReceiverRequirementSerializer,
    ServiceAreaSerializer,
)
from .services import (
    approximate_distance_km,
    normalize_area_name,
    receiver_is_currently_available,
)


class VerifiedReceiverAPIView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedReceiver,
    ]


class ServiceAreaListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request):
        areas = ServiceArea.objects.filter(
            active=True
        )

        return Response(
            ServiceAreaSerializer(
                areas,
                many=True,
            ).data
        )


class ReceiverProfileView(VerifiedReceiverAPIView):
    def get(self, request):
        profile = get_object_or_404(
            ReceiverProfile.objects.select_related(
                "service_area"
            ),
            user=request.user,
        )

        data = ReceiverProfileSerializer(
            profile
        ).data

        data["currently_available"] = (
            receiver_is_currently_available(
                request.user
            )
        )

        return Response(data)

    def put(self, request):
        profile = ReceiverProfile.objects.filter(
            user=request.user
        ).first()

        serializer = ReceiverProfileSerializer(
            profile,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=(
                status.HTTP_200_OK
                if profile
                else status.HTTP_201_CREATED
            ),
        )

    def patch(self, request):
        profile = get_object_or_404(
            ReceiverProfile,
            user=request.user,
        )

        serializer = ReceiverProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)


class ReceiverPreferenceListCreateView(
    VerifiedReceiverAPIView
):
    def get(self, request):
        preferences = (
            ReceiverPreference.objects
            .filter(receiver=request.user)
            .select_related("category")
        )

        return Response(
            ReceiverPreferenceSerializer(
                preferences,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = ReceiverPreferenceSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        category = serializer.validated_data[
            "category"
        ]

        preference, created = (
            ReceiverPreference.objects.update_or_create(
                receiver=request.user,
                category=category,
                defaults={
                    "active": serializer.validated_data.get(
                        "active",
                        True,
                    )
                },
            )
        )

        return Response(
            ReceiverPreferenceSerializer(
                preference
            ).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class ReceiverPreferenceDetailView(
    VerifiedReceiverAPIView
):
    def patch(self, request, preference_id):
        preference = get_object_or_404(
            ReceiverPreference,
            pk=preference_id,
            receiver=request.user,
        )

        serializer = ReceiverPreferenceSerializer(
            preference,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)

    def delete(self, request, preference_id):
        preference = get_object_or_404(
            ReceiverPreference,
            pk=preference_id,
            receiver=request.user,
        )

        preference.active = False
        preference.save(
            update_fields=[
                "active",
                "updated_at",
            ]
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class ReceiverRequirementListCreateView(
    VerifiedReceiverAPIView
):
    def get(self, request):
        requirements = (
            ReceiverRequirement.objects
            .filter(receiver=request.user)
            .select_related("category")
        )

        return Response(
            ReceiverRequirementSerializer(
                requirements,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = ReceiverRequirementSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data

        requirement, created = (
            ReceiverRequirement.objects.update_or_create(
                receiver=request.user,
                category=validated_data["category"],
                unit=validated_data["unit"],
                defaults={
                    "quantity_needed": (
                        validated_data[
                            "quantity_needed"
                        ]
                    ),
                    "needed_until": (
                        validated_data.get(
                            "needed_until"
                        )
                    ),
                    "active": validated_data.get(
                        "active",
                        True,
                    ),
                },
            )
        )

        return Response(
            ReceiverRequirementSerializer(
                requirement
            ).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class ReceiverRequirementDetailView(
    VerifiedReceiverAPIView
):
    def patch(self, request, requirement_id):
        requirement = get_object_or_404(
            ReceiverRequirement,
            pk=requirement_id,
            receiver=request.user,
        )

        serializer = ReceiverRequirementSerializer(
            requirement,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        quantity_needed = (
            serializer.validated_data.get(
                "quantity_needed",
                requirement.quantity_needed,
            )
        )

        if (
            quantity_needed
            < requirement.quantity_reserved
        ):
            return Response(
                {
                    "quantity_needed": (
                        "Quantity needed cannot be lower "
                        "than the currently reserved quantity."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return Response(serializer.data)

    def delete(self, request, requirement_id):
        requirement = get_object_or_404(
            ReceiverRequirement,
            pk=requirement_id,
            receiver=request.user,
        )

        requirement.active = False
        requirement.save(
            update_fields=[
                "active",
                "updated_at",
            ]
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class ReceiverAvailabilityListCreateView(
    VerifiedReceiverAPIView
):
    def get(self, request):
        availability = (
            ReceiverAvailability.objects
            .filter(receiver=request.user)
        )

        return Response(
            ReceiverAvailabilitySerializer(
                availability,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = ReceiverAvailabilitySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            availability = serializer.save(
                receiver=request.user
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This availability window already "
                        "exists."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            ReceiverAvailabilitySerializer(
                availability
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ReceiverAvailabilityDetailView(
    VerifiedReceiverAPIView
):
    def patch(self, request, availability_id):
        availability = get_object_or_404(
            ReceiverAvailability,
            pk=availability_id,
            receiver=request.user,
        )

        serializer = ReceiverAvailabilitySerializer(
            availability,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This availability window already "
                        "exists."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(serializer.data)

    def delete(self, request, availability_id):
        availability = get_object_or_404(
            ReceiverAvailability,
            pk=availability_id,
            receiver=request.user,
        )

        availability.active = False
        availability.save(
            update_fields=[
                "active",
                "updated_at",
            ]
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class ReceiverDonationDiscoveryView(
    VerifiedReceiverAPIView
):
    def get(self, request):
        filter_serializer = (
            ReceiverDiscoveryFilterSerializer(
                data=request.query_params
            )
        )

        filter_serializer.is_valid(
            raise_exception=True
        )

        filters = filter_serializer.validated_data

        profile = get_object_or_404(
            ReceiverProfile.objects.select_related(
                "service_area"
            ),
            user=request.user,
            operational=True,
            service_area__active=True,
        )

        if not receiver_is_currently_available(
            request.user
        ):
            return Response(
                {
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "distance_basis": (
                        "Approximate straight-line distance "
                        "between area centres. This is not "
                        "driving distance or travel time."
                    ),
                    "results": [],
                }
            )

        active_allocation_count = (
            DonationRequest.objects.filter(
                receiver=request.user,
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

        remaining_allocation_slots = max(
            profile.max_active_allocations
            - active_allocation_count,
            0,
        )

        if remaining_allocation_slots == 0:
            return Response(
                {
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "remaining_allocation_slots": 0,
                    "distance_basis": (
                        "Approximate straight-line distance "
                        "between area centres. This is not "
                        "driving distance or travel time."
                    ),
                    "results": [],
                }
            )

        today = timezone.localdate()

        preferences = (
            ReceiverPreference.objects.filter(
                receiver=request.user,
                active=True,
                category__active=True,
            )
            .select_related("category")
        )

        accepted_category_ids = {
            preference.category_id
            for preference in preferences
        }

        requested_category_id = filters.get(
            "category_id"
        )

        if requested_category_id:
            if (
                requested_category_id
                not in accepted_category_ids
            ):
                return Response(
                    {
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "remaining_allocation_slots": (
                            remaining_allocation_slots
                        ),
                        "distance_basis": (
                            "Approximate straight-line "
                            "distance between area centres. "
                            "This is not driving distance or "
                            "travel time."
                        ),
                        "results": [],
                    }
                )

            accepted_category_ids = {
                requested_category_id
            }

        requirements = (
            ReceiverRequirement.objects.filter(
                receiver=request.user,
                active=True,
                category_id__in=accepted_category_ids,
            )
            .filter(
                Q(needed_until__isnull=True)
                | Q(needed_until__gte=today)
            )
            .select_related("category")
        )

        requested_unit = filters.get("unit")

        requirement_map = {}

        for requirement in requirements:
            if (
                requested_unit
                and requirement.unit != requested_unit
            ):
                continue

            if requirement.remaining_quantity <= 0:
                continue

            requirement_map[
                (
                    requirement.category_id,
                    requirement.unit,
                )
            ] = requirement

        if not requirement_map:
            return Response(
                {
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "remaining_allocation_slots": (
                        remaining_allocation_slots
                    ),
                    "distance_basis": (
                        "Approximate straight-line distance "
                        "between area centres. This is not "
                        "driving distance or travel time."
                    ),
                    "results": [],
                }
            )

        service_areas = ServiceArea.objects.filter(
            active=True
        )

        area_map = {}

        for area in service_areas:
            area_map[
                normalize_area_name(area.name)
            ] = area

            area_map[
                normalize_area_name(area.code)
            ] = area

        revision_queryset = (
            DonationRevision.objects
            .filter(is_current=True)
            .select_related("category")
        )

        donations = (
            Donation.objects
            .filter(
                status=Donation.Status.AVAILABLE,
                revisions__is_current=True,
                revisions__pickup_deadline__gt=(
                    timezone.now()
                ),
                revisions__category_id__in=(
                    accepted_category_ids
                ),
            )
            .exclude(donor=request.user)
            .select_related("donor")
            .prefetch_related(
                Prefetch(
                    "revisions",
                    queryset=revision_queryset,
                    to_attr="current_revision_cache",
                )
            )
            .distinct()
        )

        pickup_before = filters.get(
            "pickup_before"
        )

        if pickup_before:
            donations = donations.filter(
                revisions__is_current=True,
                revisions__pickup_deadline__lte=(
                    pickup_before
                ),
            )

        profile_limit = float(
            profile.max_service_distance_km
        )

        requested_limit = filters.get(
            "max_distance_km"
        )

        if requested_limit is not None:
            maximum_distance = min(
                profile_limit,
                float(requested_limit),
            )
        else:
            maximum_distance = profile_limit

        candidates = []

        for donation in donations:
            cached_revisions = getattr(
                donation,
                "current_revision_cache",
                [],
            )

            if not cached_revisions:
                continue

            revision = cached_revisions[0]

            requirement = requirement_map.get(
                (
                    revision.category_id,
                    revision.unit,
                )
            )

            if requirement is None:
                continue

            if (
                revision.quantity
                > requirement.remaining_quantity
            ):
                continue

            donation_area = area_map.get(
                normalize_area_name(
                    revision.pickup_area
                )
            )

            if donation_area is None:
                continue

            distance = approximate_distance_km(
                profile.service_area.latitude,
                profile.service_area.longitude,
                donation_area.latitude,
                donation_area.longitude,
            )

            if distance > maximum_distance:
                continue

            candidates.append(
                {
                    "donation_id": str(donation.id),
                    "donor_name": (
                        donation.donor.display_name
                    ),
                    "food_name": revision.food_name,
                    "category": {
                        "id": str(revision.category.id),
                        "code": revision.category.code,
                        "name": revision.category.name,
                    },
                    "quantity": str(
                        revision.quantity
                    ),
                    "unit": revision.unit,
                    "pickup_area": (
                        revision.pickup_area
                    ),
                    "pickup_starts_at": (
                        revision.pickup_starts_at
                    ),
                    "pickup_deadline": (
                        revision.pickup_deadline
                    ),
                    "approx_distance_km": round(
                        distance,
                        2,
                    ),
                    "distance_label": (
                        f"Approximately "
                        f"{distance:.2f} km straight-line "
                        f"between area centres"
                    ),
                    "remaining_required_quantity": (
                        str(
                            requirement.remaining_quantity
                        )
                    ),
                    "compatibility_reasons": [
                        (
                            "Accepted food category"
                        ),
                        (
                            "Matching quantity unit"
                        ),
                        (
                            "Quantity fits remaining need"
                        ),
                        (
                            "Within configured service "
                            "distance"
                        ),
                        (
                            "Pickup deadline is active"
                        ),
                    ],
                }
            )

        ordering = filters.get(
            "ordering",
            "deadline",
        )

        if ordering == "distance":
            candidates.sort(
                key=lambda item: (
                    item["approx_distance_km"],
                    item["pickup_deadline"],
                )
            )

        elif ordering == "quantity":
            candidates.sort(
                key=lambda item: Decimal(
                    item["quantity"]
                )
            )

        elif ordering == "-quantity":
            candidates.sort(
                key=lambda item: Decimal(
                    item["quantity"]
                ),
                reverse=True,
            )

        else:
            candidates.sort(
                key=lambda item: (
                    item["pickup_deadline"],
                    item["approx_distance_km"],
                )
            )

        page = filters.get("page", 1)
        page_size = filters.get(
            "page_size",
            20,
        )

        total_count = len(candidates)
        start = (page - 1) * page_size
        end = start + page_size

        next_page = (
            page + 1
            if end < total_count
            else None
        )

        previous_page = (
            page - 1
            if page > 1
            else None
        )

        return Response(
            {
                "count": total_count,
                "next": next_page,
                "previous": previous_page,
                "remaining_allocation_slots": (
                    remaining_allocation_slots
                ),
                "distance_basis": (
                    "Approximate straight-line distance "
                    "between area centres. This is not "
                    "driving distance or travel time."
                ),
                "results": candidates[start:end],
            }
        )