from django.urls import path

from .complaint_views import (
    ComplaintAdminUpdateView,
    ComplaintDetailView,
    ComplaintListCreateView,
)

from .views import (
    ApproveVerificationView,
    RejectVerificationView,
    ReopenParticipantVerificationView,
    SuspendParticipantView,
    VerificationDetailView,
    VerificationDocumentDownloadView,
    VerificationHistoryView,
    VerificationListCreateView,
)


app_name = "moderation"


urlpatterns = [
    path(
        "verifications/",
        VerificationListCreateView.as_view(),
        name="verification-list-create",
    ),
    path(
        "verifications/history/",
        VerificationHistoryView.as_view(),
        name="verification-history",
    ),
    path(
        "verifications/<uuid:submission_id>/",
        VerificationDetailView.as_view(),
        name="verification-detail",
    ),
    path(
        (
            "verifications/"
            "<uuid:submission_id>/approve/"
        ),
        ApproveVerificationView.as_view(),
        name="verification-approve",
    ),
    path(
        (
            "verifications/"
            "<uuid:submission_id>/reject/"
        ),
        RejectVerificationView.as_view(),
        name="verification-reject",
    ),
    path(
        (
            "verification-documents/"
            "<uuid:document_id>/download/"
        ),
        VerificationDocumentDownloadView.as_view(),
        name="document-download",
    ),
    path(
        "admin/users/<uuid:user_id>/suspend/",
        SuspendParticipantView.as_view(),
        name="participant-suspend",
    ),
    path(
        (
            "admin/users/"
            "<uuid:user_id>/"
            "reopen-verification/"
        ),
        ReopenParticipantVerificationView.as_view(),
        name="participant-reopen",
    ),

    path(
        "complaints/",
        ComplaintListCreateView.as_view(),
        name="complaint-list-create",
    ),
    path(
        "complaints/<uuid:complaint_id>/",
        ComplaintDetailView.as_view(),
        name="complaint-detail",
    ),
    path(
        (
            "complaints/"
            "<uuid:complaint_id>/review/"
        ),
        ComplaintAdminUpdateView.as_view(),
        name="complaint-review",
    ),
]