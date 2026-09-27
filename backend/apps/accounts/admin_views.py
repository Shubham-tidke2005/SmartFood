from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdministrator


class AdminUserListView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def get(self, request):
        queryset = User.objects.all().order_by(
            "-created_at",
        )

        role = request.query_params.get(
            "role"
        )

        verification_status = (
            request.query_params.get(
                "verification_status"
            )
        )

        search = (
            request.query_params.get(
                "search",
                "",
            ).strip()
        )

        if role:
            if role not in User.Role.values:
                return Response(
                    {
                        "role": (
                            "Invalid user role."
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                role=role,
            )

        if verification_status:
            if (
                verification_status
                not in User
                .VerificationStatus.values
            ):
                return Response(
                    {
                        "verification_status": (
                            "Invalid verification "
                            "status."
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                verification_status=(
                    verification_status
                ),
            )

        if search:
            queryset = queryset.filter(
                Q(
                    display_name__icontains=(
                        search
                    )
                )
                | Q(
                    email__icontains=search
                )
                | Q(
                    mobile__icontains=search
                )
            )

        results = [
            {
                "id": user.id,
                "display_name": (
                    user.display_name
                ),
                "email": user.email,
                "mobile": user.mobile,
                "role": user.role,
                "verification_status": (
                    user.verification_status
                ),
                "contact_verified_at": (
                    user.contact_verified_at
                ),
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in queryset
        ]

        return Response(results)