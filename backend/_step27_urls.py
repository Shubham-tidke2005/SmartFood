"""Validation-only mounting; each application's URL order is unchanged."""
from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.moderation.urls")),
    *[path(f"api/{name}/", include(f"apps.{name}.urls")) for name in (
        "donations", "receivers", "logistics", "notifications", "analytics", "recommendations",
    )],
]
