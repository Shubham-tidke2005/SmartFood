from django.shortcuts import (
    get_object_or_404,
)
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsAdministrator,
)

from .complaints import Complaint
from .complaint_serializers import (
    ComplaintAdminUpdateSerializer,
    ComplaintSerializer,
)


class ComplaintListCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        user = request.user

        if (
            user.role == User.Role.ADMIN
            and user.is_staff
        ):
            queryset = (
                Complaint.objects.select_related(
                    "reporter",
                    "reported_user",
                    "assigned_to",
                    "donation",
                ).all()
            )
        else:
            queryset = (
                Complaint.objects.select_related(
                    "reporter",
                    "reported_user",
                    "assigned_to",
                    "donation",
                ).filter(
                    reporter=user,
                )
            )

        complaint_status = (
            request.query_params.get(
                "status"
            )
        )

        complaint_type = (
            request.query_params.get(
                "type"
            )
        )

        if complaint_status:
            if (
                complaint_status
                not in Complaint.Status.values
            ):
                return Response(
                    {
                        "status": (
                            "Invalid complaint status."
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                status=complaint_status,
            )

        if complaint_type:
            if (
                complaint_type
                not in Complaint
                .ComplaintType.values
            ):
                return Response(
                    {
                        "type": (
                            "Invalid complaint type."
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                complaint_type=complaint_type,
            )

        serializer = ComplaintSerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ComplaintSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        complaint = serializer.save(
            reporter=request.user,
        )

        response_serializer = (
            ComplaintSerializer(
                complaint,
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ComplaintDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_complaint(
        self,
        request,
        complaint_id,
    ):
        queryset = (
            Complaint.objects.select_related(
                "reporter",
                "reported_user",
                "assigned_to",
                "donation",
            )
        )

        if (
            request.user.role
            == User.Role.ADMIN
            and request.user.is_staff
        ):
            return get_object_or_404(
                queryset,
                id=complaint_id,
            )

        return get_object_or_404(
            queryset,
            id=complaint_id,
            reporter=request.user,
        )

    def get(
        self,
        request,
        complaint_id,
    ):
        complaint = self.get_complaint(
            request,
            complaint_id,
        )

        serializer = ComplaintSerializer(
            complaint,
        )

        return Response(serializer.data)


class ComplaintAdminUpdateView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def patch(
        self,
        request,
        complaint_id,
    ):
        complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
        )

        serializer = (
            ComplaintAdminUpdateSerializer(
                complaint,
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_complaint = (
            serializer.save()
        )

        if (
            updated_complaint.status
            in {
                Complaint.Status.RESOLVED,
                Complaint.Status.REJECTED,
            }
        ):
            if (
                updated_complaint
                .resolved_at
                is None
            ):
                updated_complaint.resolved_at = (
                    timezone.now()
                )

                updated_complaint.save(
                    update_fields=[
                        "resolved_at",
                    ]
                )

        elif (
            updated_complaint
            .resolved_at
            is not None
        ):
            updated_complaint.resolved_at = None

            updated_complaint.save(
                update_fields=[
                    "resolved_at",
                ]
            )

        response_serializer = (
            ComplaintSerializer(
                updated_complaint,
            )
        )

        return Response(
            response_serializer.data
        )