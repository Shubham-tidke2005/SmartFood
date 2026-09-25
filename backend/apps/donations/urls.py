from django.urls import path

from .views import DonationCreateView


app_name = "donations"


urlpatterns = [
    path(
        "",
        DonationCreateView.as_view(),
        name="create",
    ),
]