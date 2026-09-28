from django.contrib import admin

from .models import (
    MatchTrainingRecord,
    RecommendationCandidate,
    RecommendationEvaluation,
    RecommendationRun,
)


class RecommendationCandidateInline(
    admin.TabularInline
):
    model = RecommendationCandidate
    extra = 0
    can_delete = False

    readonly_fields = [
        "rank",
        "receiver",
        "score",
        "approximate_distance_km",
        "remaining_capacity",
        "created_at",
    ]


class RecommendationEvaluationInline(
    admin.TabularInline
):
    model = RecommendationEvaluation
    extra = 0
    can_delete = False

    readonly_fields = [
        "receiver",
        "eligible",
        "baseline_score",
        "rejection_reasons",
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
        "considered_count",
        "eligible_count",
        "candidate_count",
        "created_at",
    ]

    list_filter = [
        "algorithm",
        "status",
        "created_at",
    ]

    search_fields = [
        "id",
        "donation__id",
        "requested_by__email",
    ]

    readonly_fields = [
        "id",
        "donation",
        "revision",
        "requested_by",
        "algorithm",
        "model_version",
        "status",
        "weights",
        "considered_count",
        "eligible_count",
        "candidate_count",
        "error_message",
        "created_at",
    ]

    inlines = [
        RecommendationCandidateInline,
        RecommendationEvaluationInline,
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
        "remaining_capacity",
    ]

    list_filter = [
        "run__algorithm",
        "created_at",
    ]

    search_fields = [
        "receiver__email",
        "receiver__display_name",
        "run__id",
    ]

    readonly_fields = [
        "id",
        "run",
        "receiver",
        "rank",
        "score",
        "approximate_distance_km",
        "remaining_capacity",
        "feature_snapshot",
        "explanations",
        "created_at",
    ]


@admin.register(RecommendationEvaluation)
class RecommendationEvaluationAdmin(
    admin.ModelAdmin
):
    list_display = [
        "run",
        "receiver",
        "eligible",
        "baseline_score",
        "created_at",
    ]

    list_filter = [
        "eligible",
        "created_at",
    ]

    search_fields = [
        "receiver__email",
        "receiver__display_name",
        "run__id",
    ]

    readonly_fields = [
        "id",
        "run",
        "receiver",
        "eligible",
        "rejection_reasons",
        "eligibility_checks",
        "feature_snapshot",
        "baseline_score",
        "created_at",
    ]


@admin.register(MatchTrainingRecord)
class MatchTrainingRecordAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "donation_request",
        "dataset_source",
        "target_completed",
        "baseline_version",
        "baseline_score",
        "approved_at",
        "outcome_at",
    ]

    list_filter = [
        "dataset_source",
        "target_completed",
        "baseline_version",
        "approved_at",
    ]

    search_fields = [
        "id",
        "donation_request__id",
        "donation_request__donation__id",
        "donation_request__receiver__email",
    ]

    readonly_fields = [
        "id",
        "donation_request",
        "recommendation_evaluation",
        "dataset_source",
        "target_completed",
        "approved_at",
        "outcome_at",
        "failure_reason",
        "feature_snapshot",
        "baseline_version",
        "baseline_score",
        "recommendation_timestamp",
        "collected_at",
    ]

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False