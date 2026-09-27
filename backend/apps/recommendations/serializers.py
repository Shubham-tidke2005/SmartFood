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

    class Meta:
        model = RecommendationCandidate

        fields = [
            "id",
            "rank",
            "receiver_id",
            "receiver_name",
            "organization_name",
            "score",
            "approximate_distance_km",
            "remaining_capacity",
            "feature_snapshot",
            "explanations",
        ]

    def get_organization_name(self, obj):
        return obj.feature_snapshot.get(
            "organization_name",
            obj.receiver.display_name,
        )


class RecommendationRunSerializer(
    serializers.ModelSerializer
):
    candidates = RecommendationCandidateSerializer(
        many=True,
        read_only=True,
    )

    donation_id = serializers.UUIDField(
        source="donation.id",
        read_only=True,
    )

    revision_id = serializers.UUIDField(
        source="revision.id",
        read_only=True,
    )

    class Meta:
        model = RecommendationRun

        fields = [
            "id",
            "donation_id",
            "revision_id",
            "algorithm",
            "model_version",
            "status",
            "weights",
            "candidate_count",
            "created_at",
            "candidates",
        ]