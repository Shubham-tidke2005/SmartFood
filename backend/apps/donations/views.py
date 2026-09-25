from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVerifiedDonor

from .serializers import (
    DonationCreateSerializer,
    DonationReadSerializer,
)


class DonationCreateView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsVerifiedDonor,
    ]

    def post(self, request):
        serializer = DonationCreateSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        donation = serializer.save()

        return Response(
            DonationReadSerializer(donation).data,
            status=status.HTTP_201_CREATED,
        )