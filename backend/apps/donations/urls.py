from django.urls import path

from .request_views import (
    DonationArrangementCancelView,
    DonationCancelView,
    DonationRequestApproveView,
    DonationRequestCreateView,
    DonationRequestListView,
    DonationRequestRejectView,
    DonationRequestWithdrawView,
)
from .views import (
    DonationDetailView,
    DonationHistoryView,
    DonationImageUploadView,
    DonationListCreateView,
    DonationRevisionCreateView,
    FoodCategoryListView,
)


app_name = "donations"


urlpatterns = [
    path(
        "food-categories/",
        FoodCategoryListView.as_view(),
        name="food-category-list",
    ),
    path(
        "",
        DonationListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "requests/",
        DonationRequestListView.as_view(),
        name="request-list",
    ),
    path(
        "requests/<uuid:request_id>/withdraw/",
        DonationRequestWithdrawView.as_view(),
        name="request-withdraw",
    ),
    path(
        "requests/<uuid:request_id>/approve/",
        DonationRequestApproveView.as_view(),
        name="request-approve",
    ),
    path(
        "requests/<uuid:request_id>/reject/",
        DonationRequestRejectView.as_view(),
        name="request-reject",
    ),
    path(
        (
            "requests/<uuid:request_id>/"
            "cancel-arrangement/"
        ),
        DonationArrangementCancelView.as_view(),
        name="arrangement-cancel",
    ),
    path(
        "<uuid:donation_id>/",
        DonationDetailView.as_view(),
        name="detail",
    ),
    path(
        "<uuid:donation_id>/revisions/",
        DonationRevisionCreateView.as_view(),
        name="revision-create",
    ),
    path(
        "<uuid:donation_id>/images/",
        DonationImageUploadView.as_view(),
        name="image-upload",
    ),
    path(
        "<uuid:donation_id>/cancel/",
        DonationCancelView.as_view(),
        name="cancel",
    ),
    path(
        "<uuid:donation_id>/history/",
        DonationHistoryView.as_view(),
        name="history",
    ),
    path(
        "<uuid:donation_id>/requests/",
        DonationRequestCreateView.as_view(),
        name="request-create",
    ),
]