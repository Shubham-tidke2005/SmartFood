from pathlib import Path

from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsVerifiedDonor,
    IsVerifiedReceiver,
)

from .models import (
    Donation,
    DonationImage,
    DonationRequest,
    DonationRevision,
    FoodCategory,
)
from .serializers import (
    DonationCancellationSerializer,
    DonationFilterSerializer,
    DonationImageSerializer,
    DonationImageUploadSerializer,
    DonationReadSerializer,
    DonationRequestCreateSerializer,
    DonationRequestReadSerializer,
    DonationStatusHistorySerializer,
    DonationWriteSerializer,
    FoodCategorySerializer,
)
from .services import (
    expire_donation_if_required,
    record_donation_history,
)


class DonationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def current_revision_prefetch():
    return Prefetch(
        "revisions",
        queryset=(
            DonationRevision.objects
            .filter(is_current=True)
            .select_related("category")
            .prefetch_related("images")
        ),
        to_attr="current_revision_cache",
    )


def user_is_admin(user):
    return bool(
        user.role == User.Role.ADMIN
        and user.is_staff
    )


def user_can_view_private_donation(
    user,
    donation,
):
    if user_is_admin(user):
        return True

    if donation.donor_id == user.id:
        return True

    return donation.requests.filter(
        receiver=user
    ).exists()


def create_images(revision, uploaded_images):
    for position, uploaded_image in enumerate(
        uploaded_images
    ):
        DonationImage.objects.create(
            revision=revision,
            image=uploaded_image,
            original_name=Path(
                uploaded_image.name
            ).name,
            mime_type=uploaded_image.content_type,
            size_bytes=uploaded_image.size,
            position=position,
        )


class FoodCategoryListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request):
        categories = FoodCategory.objects.filter(
            active=True
        )

        return Response(
            FoodCategorySerializer(
                categories,
                many=True,
            ).data
        )


class DonationListCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def get(self, request):
        filter_serializer = DonationFilterSerializer(
            data=request.query_params
        )

        filter_serializer.is_valid(
            raise_exception=True
        )

        filters = filter_serializer.validated_data
        mine = filters.get("mine", False)

        queryset = (
            Donation.objects
            .select_related("donor")
            .prefetch_related(
                current_revision_prefetch()
            )
        )

        if mine:
            if request.user.role == User.Role.DONOR:
                queryset = queryset.filter(
                    donor=request.user
                )

            elif request.user.role == User.Role.RECEIVER:
                queryset = queryset.filter(
                    requests__receiver=request.user
                )

            elif not user_is_admin(request.user):
                queryset = queryset.none()

        else:
            queryset = queryset.filter(
                status=Donation.Status.AVAILABLE,
                revisions__is_current=True,
                revisions__pickup_deadline__gt=(
                    timezone.now()
                ),
            )

        requested_status = filters.get("status")

        if requested_status:
            if not mine and not user_is_admin(
                request.user
            ):
                return Response(
                    {
                        "status": (
                            "Status filtering is only available "
                            "for your own history."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(
                status=requested_status
            )

        if category_id := filters.get("category_id"):
            queryset = queryset.filter(
                revisions__is_current=True,
                revisions__category_id=category_id,
            )

        if unit := filters.get("unit"):
            queryset = queryset.filter(
                revisions__is_current=True,
                revisions__unit=unit,
            )

        if minimum := filters.get("min_quantity"):
            queryset = queryset.filter(
                revisions__is_current=True,
                revisions__quantity__gte=minimum,
            )

        if maximum := filters.get("max_quantity"):
            queryset = queryset.filter(
                revisions__is_current=True,
                revisions__quantity__lte=maximum,
            )

        if pickup_before := filters.get(
            "pickup_before"
        ):
            queryset = queryset.filter(
                revisions__is_current=True,
                revisions__pickup_deadline__lte=(
                    pickup_before
                ),
            )

        if search := filters.get("search"):
            queryset = queryset.filter(
                Q(
                    revisions__is_current=True,
                    revisions__food_name__icontains=(
                        search
                    ),
                )
                | Q(
                    revisions__is_current=True,
                    revisions__description__icontains=(
                        search
                    ),
                )
            )

        ordering = filters["ordering"]

        ordering_map = {
            "newest": "-published_at",
            "deadline": (
                "revisions__pickup_deadline"
            ),
            "quantity": "revisions__quantity",
            "-quantity": "-revisions__quantity",
        }

        queryset = (
            queryset
            .order_by(ordering_map[ordering])
            .distinct()
        )

        paginator = DonationPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = DonationReadSerializer(
            page,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        permission = IsVerifiedDonor()

        if not permission.has_permission(
            request,
            self,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DonationWriteSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data
        uploaded_images = validated_data.pop(
            "images",
            [],
        )

        with transaction.atomic():
            donation = Donation.objects.create(
                donor=request.user,
                status=Donation.Status.AVAILABLE,
            )

            revision = DonationRevision.objects.create(
                donation=donation,
                number=1,
                is_current=True,
                proposed_by=request.user,
                **validated_data,
            )

            create_images(
                revision,
                uploaded_images,
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="CREATED",
                from_status="",
                to_status=Donation.Status.AVAILABLE,
                reason="Donation listing created.",
            )

        output = DonationReadSerializer(
            donation,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class DonationDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, donation_id):
        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects
                .select_for_update()
                .select_related("donor")
                .prefetch_related(
                    current_revision_prefetch()
                ),
                pk=donation_id,
            )

            expire_donation_if_required(donation)

        if (
            donation.status
            != Donation.Status.AVAILABLE
            and not user_can_view_private_donation(
                request.user,
                donation,
            )
        ):
            return Response(
                {
                    "detail": "Donation not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            DonationReadSerializer(
                donation,
                context={
                    "request": request,
                },
            ).data
        )


class DonationRevisionCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedDonor,
    ]

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, donation_id):
        serializer = DonationWriteSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data
        uploaded_images = validated_data.pop(
            "images",
            None,
        )

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=donation_id,
            )

            if donation.donor_id != request.user.id:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner can "
                            "edit this listing."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            expire_donation_if_required(donation)

            if (
                donation.status
                != Donation.Status.AVAILABLE
            ):
                return Response(
                    {
                        "detail": (
                            "Only an available donation can "
                            "be edited."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            current_revision = get_object_or_404(
                DonationRevision.objects
                .select_for_update()
                .prefetch_related("images"),
                donation=donation,
                is_current=True,
            )

            current_revision.is_current = False

            current_revision.save(
                update_fields=[
                    "is_current",
                    "updated_at",
                ]
            )

            new_revision = (
                DonationRevision.objects.create(
                    donation=donation,
                    number=current_revision.number + 1,
                    is_current=True,
                    proposed_by=request.user,
                    **validated_data,
                )
            )

            if uploaded_images is None:
                for old_image in current_revision.images.all():
                    DonationImage.objects.create(
                        revision=new_revision,
                        image=old_image.image.name,
                        original_name=old_image.original_name,
                        mime_type=old_image.mime_type,
                        size_bytes=old_image.size_bytes,
                        position=old_image.position,
                    )

            else:
                create_images(
                    new_revision,
                    uploaded_images,
                )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="REVISION_CREATED",
                from_status=donation.status,
                to_status=donation.status,
                reason=(
                    f"Donation revision "
                    f"{new_revision.number} created."
                ),
            )

        return Response(
            DonationReadSerializer(
                donation,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DonationImageUploadView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedDonor,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, donation_id):
        serializer = DonationImageUploadSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        uploaded_images = serializer.validated_data[
            "images"
        ]

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=donation_id,
            )

            if donation.donor_id != request.user.id:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner can "
                            "upload listing images."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            expire_donation_if_required(donation)

            if (
                donation.status
                != Donation.Status.AVAILABLE
            ):
                return Response(
                    {
                        "detail": (
                            "Images can only be added to an "
                            "available donation."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            revision = get_object_or_404(
                DonationRevision.objects
                .select_for_update(),
                donation=donation,
                is_current=True,
            )

            existing_count = revision.images.count()

            if (
                existing_count + len(uploaded_images)
                > 5
            ):
                return Response(
                    {
                        "images": (
                            "A donation can contain at most "
                            "five images."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_images = []

            for offset, uploaded_image in enumerate(
                uploaded_images
            ):
                created_images.append(
                    DonationImage.objects.create(
                        revision=revision,
                        image=uploaded_image,
                        original_name=Path(
                            uploaded_image.name
                        ).name,
                        mime_type=(
                            uploaded_image.content_type
                        ),
                        size_bytes=uploaded_image.size,
                        position=existing_count + offset,
                    )
                )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="IMAGES_ADDED",
                from_status=donation.status,
                to_status=donation.status,
                reason=(
                    f"{len(created_images)} image(s) added."
                ),
            )

        return Response(
            DonationImageSerializer(
                created_images,
                many=True,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DonationCancelView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, donation_id):
        serializer = DonationCancellationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        reason = serializer.validated_data["reason"]

        with transaction.atomic():
            donation = get_object_or_404(
                Donation.objects.select_for_update(),
                pk=donation_id,
            )

            authorized = (
                donation.donor_id == request.user.id
                or user_is_admin(request.user)
            )

            if not authorized:
                return Response(
                    {
                        "detail": (
                            "Only the donation owner or an "
                            "administrator can cancel it."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            expire_donation_if_required(donation)

            if donation.status not in {
                Donation.Status.AVAILABLE,
                Donation.Status.RESERVED,
            }:
                return Response(
                    {
                        "detail": (
                            "This donation can no longer "
                            "be cancelled."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            previous_status = donation.status
            current_time = timezone.now()

            donation.status = Donation.Status.CANCELLED
            donation.closed_at = current_time

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            donation.requests.filter(
                status=DonationRequest.Status.PENDING
            ).update(
                status=DonationRequest.Status.CANCELLED,
                decided_at=current_time,
                reason="Donation cancelled.",
                updated_at=current_time,
            )

            record_donation_history(
                donation=donation,
                actor=request.user,
                event_type="CANCELLED",
                from_status=previous_status,
                to_status=Donation.Status.CANCELLED,
                reason=reason,
            )

        return Response(
            DonationReadSerializer(
                donation,
                context={
                    "request": request,
                },
            ).data
        )


class DonationHistoryView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, donation_id):
        donation = get_object_or_404(
            Donation,
            pk=donation_id,
        )

        if not user_can_view_private_donation(
            request.user,
            donation,
        ):
            return Response(
                {
                    "detail": "Donation not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        history = donation.status_history.select_related(
            "actor"
        )

        return Response(
            DonationStatusHistorySerializer(
                history,
                many=True,
            ).data
        )


class DonationRequestCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedReceiver,
    ]

    def post(self, request, donation_id):
        serializer = DonationRequestCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            with transaction.atomic():
                donation = get_object_or_404(
                    Donation.objects
                    .select_for_update(),
                    pk=donation_id,
                )

                expire_donation_if_required(donation)

                if (
                    donation.status
                    != Donation.Status.AVAILABLE
                ):
                    return Response(
                        {
                            "detail": (
                                "The donation is unavailable "
                                "or expired."
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                current_revision = get_object_or_404(
                    DonationRevision.objects
                    .select_for_update(),
                    donation=donation,
                    is_current=True,
                )

                if (
                    current_revision.pickup_deadline
                    <= timezone.now()
                ):
                    expire_donation_if_required(donation)

                    return Response(
                        {
                            "detail": (
                                "The donation pickup deadline "
                                "has passed."
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                donation_request = (
                    DonationRequest.objects.create(
                        donation=donation,
                        receiver=request.user,
                        requested_revision=current_revision,
                        proposed_mode=(
                            serializer.validated_data[
                                "proposed_mode"
                            ]
                        ),
                        expires_at=(
                            current_revision.pickup_deadline
                        ),
                    )
                )

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "You already have an active request "
                        "for this donation."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            DonationRequestReadSerializer(
                donation_request
            ).data,
            status=status.HTTP_201_CREATED,
        )