from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        queryset = Notification.objects.filter(
            recipient=request.user,
        ).order_by(
            "-created_at",
        )

        unread = request.query_params.get(
            "unread"
        )

        if unread is not None:
            normalized_unread = (
                str(unread)
                .strip()
                .lower()
            )

            if normalized_unread in {
                "1",
                "true",
                "yes",
            }:
                queryset = queryset.filter(
                    read_at__isnull=True,
                )

            elif normalized_unread in {
                "0",
                "false",
                "no",
            }:
                queryset = queryset.filter(
                    read_at__isnull=False,
                )

            else:
                return Response(
                    {
                        "unread": (
                            "Use true or false."
                        ),
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

        serializer = NotificationSerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        notification_id,
    ):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
        )

        if notification.read_at is None:
            notification.read_at = (
                timezone.now()
            )

            notification.save(
                update_fields=[
                    "read_at",
                ]
            )

        serializer = NotificationSerializer(
            notification,
        )

        return Response(serializer.data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        updated_count = (
            Notification.objects.filter(
                recipient=request.user,
                read_at__isnull=True,
            ).update(
                read_at=timezone.now(),
            )
        )

        return Response(
            {
                "detail": (
                    "Notifications marked as read."
                ),
                "updated_count": updated_count,
            }
        )