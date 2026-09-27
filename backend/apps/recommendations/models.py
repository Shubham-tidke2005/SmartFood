import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.donations.models import (
    Donation,
    DonationRevision,
)


class RecommendationRun(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    class Algorithm(models.TextChoices):
        RULE_BASED_V1 = (
            "RULE_BASED_V1",
            "Explainable weighted baseline v1",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        related_name="recommendation_runs",
    )

    revision = models.ForeignKey(
        DonationRevision,
        on_delete=models.PROTECT,
        related_name="recommendation_runs",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_recommendation_runs",
    )

    algorithm = models.CharField(
        max_length=40,
        choices=Algorithm.choices,
        default=Algorithm.RULE_BASED_V1,
    )

    model_version = models.CharField(
        max_length=50,
        default="baseline-1.0",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
        db_index=True,
    )

    weights = models.JSONField(
        default=dict,
    )

    candidate_count = models.PositiveIntegerField(
        default=0,
    )

    error_message = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "recommendation_runs"
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["donation", "-created_at"],
                name="rec_run_donation_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Recommendation run {self.id} "
            f"for {self.donation_id}"
        )


class RecommendationCandidate(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    run = models.ForeignKey(
        RecommendationRun,
        on_delete=models.CASCADE,
        related_name="candidates",
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recommendation_candidates",
    )

    rank = models.PositiveIntegerField()

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    approximate_distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    remaining_capacity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
    )

    feature_snapshot = models.JSONField(
        default=dict,
    )

    explanations = models.JSONField(
        default=list,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "recommendation_candidates"
        ordering = ["rank"]

        constraints = [
            models.UniqueConstraint(
                fields=["run", "receiver"],
                name="unique_receiver_per_rec_run",
            ),
            models.UniqueConstraint(
                fields=["run", "rank"],
                name="unique_rank_per_rec_run",
            ),
            models.CheckConstraint(
                condition=Q(score__gte=0) & Q(score__lte=100),
                name="rec_score_between_0_100",
            ),
        ]

        indexes = [
            models.Index(
                fields=["run", "rank"],
                name="rec_candidate_run_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.receiver.email}: "
            f"{self.score}"
        )