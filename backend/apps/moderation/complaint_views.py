from django.db import transaction
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

from .audit_models import AuditEvent
from .audit_services import (
    record_audit_event,
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

        queryset = (
            Complaint.objects
            .select_related(
                "reporter",
                "reported_user",
                "assigned_to",
                "donation",
            )
        )

        if not (
            user.role == User.Role.ADMIN
            and user.is_staff
        ):
            queryset = queryset.filter(
                reporter=user
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
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                status=complaint_status
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
                        )
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

            queryset = queryset.filter(
                complaint_type=complaint_type
            )

        return Response(
            ComplaintSerializer(
                queryset,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = ComplaintSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        complaint = serializer.save(
            reporter=request.user
        )

        return Response(
            ComplaintSerializer(
                complaint
            ).data,
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
            Complaint.objects
            .select_related(
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

        return Response(
            ComplaintSerializer(
                complaint
            ).data
        )


class ComplaintAdminUpdateView(APIView):
    permission_classes = [
        IsAdministrator,
    ]

    def patch(
        self,
        request,
        complaint_id,
    ):
        audit_reason = (
            request.data.get("audit_reason")
            or request.data.get("resolution")
            or ""
        ).strip()

        if len(audit_reason) < 5:
            return Response(
                {
                    "audit_reason": (
                        "Provide a reason of at least "
                        "5 characters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.data.copy()

        if hasattr(payload, "pop"):
            payload.pop(
                "audit_reason",
                None,
            )

        with transaction.atomic():
            complaint = get_object_or_404(
                Complaint.objects
                .select_for_update(),
                id=complaint_id,
            )

            old_values = {
                "status": complaint.status,
                "assigned_to_id": (
                    str(complaint.assigned_to_id)
                    if complaint.assigned_to_id
                    else None
                ),
                "resolution": (
                    complaint.resolution
                ),
                "resolved_at": (
                    complaint
                    .resolved_at
                    .isoformat()
                    if complaint.resolved_at
                    else None
                ),
            }

            serializer = (
                ComplaintAdminUpdateSerializer(
                    complaint,
                    data=payload,
                    partial=True,
                )
            )

            serializer.is_valid(
                raise_exception=True
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
            else:
                updated_complaint.resolved_at = None

            updated_complaint.save(
                update_fields=[
                    "resolved_at",
                    "updated_at",
                ]
            )

            new_values = {
                "status": (
                    updated_complaint.status
                ),
                "assigned_to_id": (
                    str(
                        updated_complaint
                        .assigned_to_id
                    )
                    if (
                        updated_complaint
                        .assigned_to_id
                    )
                    else None
                ),
                "resolution": (
                    updated_complaint
                    .resolution
                ),
                "resolved_at": (
                    updated_complaint
                    .resolved_at
                    .isoformat()
                    if (
                        updated_complaint
                        .resolved_at
                    )
                    else None
                ),
            }

            record_audit_event(
                action=(
                    AuditEvent.Action
                    .COMPLAINT_UPDATED
                ),
                target_type=(
                    "moderation.Complaint"
                ),
                target_id=(
                    updated_complaint.id
                ),
                actor=request.user,
                request=request,
                reason=audit_reason,
                old_values=old_values,
                new_values=new_values,
            )

        return Response(
            ComplaintSerializer(
                updated_complaint
            ).data
        )