from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)


app_name = "notifications"


urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="list",
    ),
    path(
        "mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="mark-all-read",
    ),
    path(
        "<uuid:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="mark-read",
    ),
]