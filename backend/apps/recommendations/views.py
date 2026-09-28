from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.donations.models import Donation

from .models import RecommendationRun
from .serializers import (
    RecommendationRunSerializer,
)
from .services import generate_recommendations


def user_can_view_recommendations(
    user,
    donation,
):
    if donation.donor_id == user.id:
        return True

    return bool(
        user.role == User.Role.ADMIN
        and user.is_staff
    )


class DonationRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get_donation(self, donation_id):
        return get_object_or_404(
            Donation.objects.select_related(
                "donor"
            ),
            pk=donation_id,
        )

    def check_access(
        self,
        request,
        donation,
    ):
        return user_can_view_recommendations(
            request.user,
            donation,
        )

    def get(self, request, donation_id):
        donation = self.get_donation(
            donation_id
        )

        if not self.check_access(
            request,
            donation,
        ):
            return Response(
                {
                    "detail": (
                        "Only the donation owner or "
                        "an administrator can view "
                        "these recommendations."
                    )
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        recommendation_run = (
            RecommendationRun.objects
            .filter(
                donation=donation,
                status=(
                    RecommendationRun.Status
                    .COMPLETED
                ),
            )
            .select_related(
                "donation",
                "revision",
                "requested_by",
            )
            .prefetch_related(
                "candidates__receiver",
                "evaluations__receiver",
            )
            .first()
        )

        if recommendation_run is None:
            return Response(
                {
                    "detail": (
                        "No recommendation run exists "
                        "for this donation."
                    )
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            RecommendationRunSerializer(
                recommendation_run
            )
        )

        return Response(serializer.data)

    def post(self, request, donation_id):
        donation = self.get_donation(
            donation_id
        )

        if not self.check_access(
            request,
            donation,
        ):
            return Response(
                {
                    "detail": (
                        "Only the donation owner or "
                        "an administrator can generate "
                        "recommendations."
                    )
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        try:
            recommendation_run = (
                generate_recommendations(
                    donation=donation,
                    requested_by=request.user,
                )
            )
        except ValueError as error:
            return Response(
                {
                    "detail": str(error)
                },
                status=(
                    status.HTTP_409_CONFLICT
                ),
            )

        serializer = (
            RecommendationRunSerializer(
                recommendation_run
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )