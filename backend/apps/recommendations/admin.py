from django.contrib import admin

from .models import (
    RecommendationCandidate,
    RecommendationRun,
)


class RecommendationCandidateInline(
    admin.TabularInline
):
    model = RecommendationCandidate
    extra = 0
    can_delete = False

    readonly_fields = [
        "receiver",
        "rank",
        "score",
        "approximate_distance_km",
        "remaining_capacity",
        "feature_snapshot",
        "explanations",
        "created_at",
    ]


@admin.register(RecommendationRun)
class RecommendationRunAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "donation",
        "algorithm",
        "model_version",
        "status",
        "candidate_count",
        "created_at",
    ]

    list_filter = [
        "algorithm",
        "status",
        "created_at",
    ]

    search_fields = [
        "donation__id",
        "donation__donor__email",
    ]

    readonly_fields = [
        "id",
        "created_at",
    ]

    inlines = [
        RecommendationCandidateInline,
    ]


@admin.register(RecommendationCandidate)
class RecommendationCandidateAdmin(
    admin.ModelAdmin
):
    list_display = [
        "run",
        "rank",
        "receiver",
        "score",
        "approximate_distance_km",
    ]

    list_filter = [
        "created_at",
    ]

    search_fields = [
        "receiver__email",
        "receiver__display_name",
        "run__donation__id",
    ]

    readonly_fields = [
        "id",
        "created_at",
    ]