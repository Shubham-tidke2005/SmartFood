from django.urls import path

from .views import (
    DonationRecommendationView,
)


app_name = "recommendations"


urlpatterns = [
    path(
        "donations/<uuid:donation_id>/",
        DonationRecommendationView.as_view(),
        name="donation-recommendations",
    ),
]