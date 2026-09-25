from django.db import connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse(
            {
                "status": "healthy",
                "application": "SmartFood API",
                "database": "connected",
            },
            status=200,
        )

    except Exception:
        return JsonResponse(
            {
                "status": "unhealthy",
                "application": "SmartFood API",
                "database": "disconnected",
            },
            status=503,
        )