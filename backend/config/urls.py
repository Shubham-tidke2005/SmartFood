from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from config.views import health_check


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "api/health/",
        health_check,
        name="health-check",
    ),
    path(
        "api/",
        include("apps.accounts.urls"),
    ),
    path(
        "api/donations/",
        include("apps.donations.urls"),
    ),
    path(
        "api/",
        include("apps.moderation.urls"),
    ),
    path(
    "api/receivers/",
    include("apps.receivers.urls"),
),
    path(
    "api/logistics/",
    include("apps.logistics.urls"),
),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )