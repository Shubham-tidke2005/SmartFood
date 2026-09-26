from django.urls import path

from .views import (
    ReceiverAvailabilityDetailView,
    ReceiverAvailabilityListCreateView,
    ReceiverDonationDiscoveryView,
    ReceiverPreferenceDetailView,
    ReceiverPreferenceListCreateView,
    ReceiverProfileView,
    ReceiverRequirementDetailView,
    ReceiverRequirementListCreateView,
    ServiceAreaListView,
)


app_name = "receivers"


urlpatterns = [
    path(
        "service-areas/",
        ServiceAreaListView.as_view(),
        name="service-area-list",
    ),
    path(
        "profile/",
        ReceiverProfileView.as_view(),
        name="profile",
    ),
    path(
        "preferences/",
        ReceiverPreferenceListCreateView.as_view(),
        name="preference-list-create",
    ),
    path(
        "preferences/<uuid:preference_id>/",
        ReceiverPreferenceDetailView.as_view(),
        name="preference-detail",
    ),
    path(
        "requirements/",
        ReceiverRequirementListCreateView.as_view(),
        name="requirement-list-create",
    ),
    path(
        "requirements/<uuid:requirement_id>/",
        ReceiverRequirementDetailView.as_view(),
        name="requirement-detail",
    ),
    path(
        "availability/",
        ReceiverAvailabilityListCreateView.as_view(),
        name="availability-list-create",
    ),
    path(
        "availability/<uuid:availability_id>/",
        ReceiverAvailabilityDetailView.as_view(),
        name="availability-detail",
    ),
    path(
        "discover-donations/",
        ReceiverDonationDiscoveryView.as_view(),
        name="discover-donations",
    ),
]