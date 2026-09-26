from django.contrib import admin

from .models import (
    VerificationDocument,
    VerificationHistory,
    VerificationSubmission,
)


class VerificationDocumentInline(
    admin.TabularInline
):
    model = VerificationDocument
    extra = 0
    can_delete = False

    fields = [
        "document_type",
        "original_name",
        "mime_type",
        "size_bytes",
        "created_at",
    ]

    readonly_fields = fields


@admin.register(VerificationSubmission)
class VerificationSubmissionAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "user",
        "attempt",
        "status",
        "reviewer",
        "created_at",
        "reviewed_at",
    ]

    list_filter = [
        "status",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "user__display_name",
    ]

    readonly_fields = [
        "id",
        "user",
        "attempt",
        "status",
        "submitted_details",
        "reviewer",
        "reviewed_at",
        "reason",
        "created_at",
        "updated_at",
    ]

    inlines = [
        VerificationDocumentInline,
    ]


@admin.register(VerificationHistory)
class VerificationHistoryAdmin(
    admin.ModelAdmin
):
    list_display = [
        "user",
        "action",
        "from_status",
        "to_status",
        "actor",
        "created_at",
    ]

    list_filter = [
        "action",
        "to_status",
    ]

    search_fields = [
        "user__email",
        "actor__email",
    ]

    readonly_fields = [
        "id",
        "user",
        "submission",
        "actor",
        "action",
        "from_status",
        "to_status",
        "reason",
        "created_at",
    ]