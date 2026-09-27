from django.urls import path

from .views import PlatformAnalyticsView


app_name = "analytics"


urlpatterns = [
    path(
        "",
        PlatformAnalyticsView.as_view(),
        name="platform-analytics",
    ),
]