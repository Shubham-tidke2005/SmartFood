from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_analytics_for_user


class AnalyticsView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        analytics = get_analytics_for_user(
            request.user
        )

        return Response(analytics)