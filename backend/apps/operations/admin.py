from django.contrib import admin

from .models import (
    BackgroundJob,
    OperationalIssue,
)


@admin.register(OperationalIssue)
class OperationalIssueAdmin(admin.ModelAdmin):
    list_display = [
        "issue_type",
        "status",
        "donation",
        "affected_user",
        "detected_at",
    ]

    list_filter = [
        "issue_type",
        "status",
        "detected_at",
    ]

    search_fields = [
        "deduplication_key",
        "summary",
        "donation__id",
        "affected_user__email",
    ]

    readonly_fields = [
        "id",
        "deduplication_key",
        "issue_type",
        "donation",
        "donation_request",
        "volunteer_task",
        "affected_user",
        "summary",
        "details",
        "detected_at",
        "created_at",
        "updated_at",
    ]

    ordering = ["-detected_at"]


@admin.register(BackgroundJob)
class BackgroundJobAdmin(admin.ModelAdmin):
    list_display = [
        "job_type",
        "status",
        "attempts",
        "max_attempts",
        "run_after",
        "completed_at",
    ]

    list_filter = [
        "job_type",
        "status",
        "run_after",
    ]

    search_fields = [
        "deduplication_key",
        "last_error",
    ]

    readonly_fields = [
        "id",
        "deduplication_key",
        "job_type",
        "payload",
        "attempts",
        "locked_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]

    ordering = ["-created_at"]