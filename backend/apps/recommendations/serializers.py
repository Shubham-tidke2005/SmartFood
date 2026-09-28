from rest_framework import serializers

from .models import (
    RecommendationCandidate,
    RecommendationRun,
)


class RecommendationCandidateSerializer(
    serializers.ModelSerializer
):
    receiver_id = serializers.UUIDField(
        source="receiver.id",
        read_only=True,
    )

    receiver_name = serializers.CharField(
        source="receiver.display_name",
        read_only=True,
    )

    organization_name = (
        serializers.SerializerMethodField()
    )

    matching_factors = (
        serializers.SerializerMethodField()
    )

    completion_probability = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = RecommendationCandidate

        fields = [
            "id",
            "rank",
            "receiver_id",
            "receiver_name",
            "organization_name",
            "score",
            "completion_probability",
            "approximate_distance_km",
            "remaining_capacity",
            "matching_factors",
            "feature_snapshot",
            "explanations",
        ]

        read_only_fields = fields

    def get_organization_name(self, obj):
        return obj.feature_snapshot.get(
            "organization_name",
            obj.receiver.display_name,
        )

    def get_matching_factors(self, obj):
        matching_factors = (
            obj.feature_snapshot.get(
                "matching_factors"
            )
        )

        if matching_factors:
            return matching_factors

        return obj.feature_snapshot.get(
            "normalized_features",
            {},
        )

    def get_completion_probability(self, obj):
        model_snapshot = (
            obj.feature_snapshot.get(
                "model",
                {},
            )
        )

        probability = model_snapshot.get(
            "completion_probability"
        )

        if probability is None:
            return None

        return float(probability)


class RecommendationRunSerializer(
    serializers.ModelSerializer
):
    candidates = (
        RecommendationCandidateSerializer(
            many=True,
            read_only=True,
        )
    )

    donation_id = serializers.UUIDField(
        source="donation.id",
        read_only=True,
    )

    revision_id = serializers.UUIDField(
        source="revision.id",
        read_only=True,
    )

    scoring_method = (
        serializers.SerializerMethodField()
    )

    fallback_used = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = RecommendationRun

        fields = [
            "id",
            "donation_id",
            "revision_id",
            "algorithm",
            "scoring_method",
            "model_version",
            "status",
            "weights",
            "considered_count",
            "eligible_count",
            "candidate_count",
            "fallback_used",
            "created_at",
            "candidates",
        ]

        read_only_fields = fields

    def get_scoring_method(self, obj):
        if (
            obj.algorithm
            == RecommendationRun.Algorithm
            .ML_COMPLETION_V1
        ):
            return "ML_COMPLETION_PROBABILITY"

        return "RULE_BASED_BASELINE"

    def get_fallback_used(self, obj):
        return bool(
            obj.error_message
            and obj.algorithm
            == RecommendationRun.Algorithm
            .RULE_BASED_V2
        )