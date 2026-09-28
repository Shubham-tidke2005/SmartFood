import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.donations.models import (
    Donation,
    DonationRequest,
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

        RULE_BASED_V2 = (
            "RULE_BASED_V2",
            "Normalized weighted baseline v2",
        )

        ML_COMPLETION_V1 = (
            "ML_COMPLETION_V1",
            "Completion probability model v1",
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
        default=Algorithm.RULE_BASED_V2,
    )

    model_version = models.CharField(
        max_length=50,
        default="baseline-2.0",
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

    considered_count = models.PositiveIntegerField(
        default=0,
    )

    eligible_count = models.PositiveIntegerField(
        default=0,
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
            models.Index(
                fields=["algorithm", "-created_at"],
                name="rec_run_algo_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Recommendation run {self.id} "
            f"for donation {self.donation_id}"
        )


class RecommendationEvaluation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    run = models.ForeignKey(
        RecommendationRun,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recommendation_evaluations",
    )

    eligible = models.BooleanField(
        default=False,
        db_index=True,
    )

    rejection_reasons = models.JSONField(
        default=list,
        blank=True,
    )

    eligibility_checks = models.JSONField(
        default=dict,
    )

    feature_snapshot = models.JSONField(
        default=dict,
    )

    baseline_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "recommendation_evaluations"
        ordering = [
            "-eligible",
            "-baseline_score",
            "created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["run", "receiver"],
                name="unique_rec_eval_receiver",
            ),
            models.CheckConstraint(
                condition=(
                    Q(baseline_score__isnull=True)
                    | (
                        Q(baseline_score__gte=0)
                        & Q(baseline_score__lte=100)
                    )
                ),
                name="rec_eval_score_0_100",
            ),
        ]

        indexes = [
            models.Index(
                fields=["run", "eligible"],
                name="rec_eval_run_eligible_idx",
            ),
        ]

    def __str__(self):
        result = (
            "eligible"
            if self.eligible
            else "ineligible"
        )

        return (
            f"{self.receiver.email}: {result}"
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
                condition=(
                    Q(score__gte=0)
                    & Q(score__lte=100)
                ),
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
            f"Rank {self.rank}: "
            f"{self.receiver.email} "
            f"({self.score})"
        )


class MatchTrainingRecord(models.Model):
    """
    One resolved, approved donation-receiver match.

    Only the saved recommendation-time feature snapshot is
    used as model input. Outcome information is stored as
    label metadata and must not be used as input features.
    """

    class DatasetSource(models.TextChoices):
        REAL = "REAL", "Real platform data"
        SYNTHETIC = (
            "SYNTHETIC",
            "Synthetically generated data",
        )
        PILOT = "PILOT", "Pilot/testing data"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation_request = models.OneToOneField(
        DonationRequest,
        on_delete=models.PROTECT,
        related_name="training_record",
    )

    recommendation_evaluation = (
        models.ForeignKey(
            RecommendationEvaluation,
            on_delete=models.PROTECT,
            related_name="training_records",
        )
    )

    dataset_source = models.CharField(
        max_length=20,
        choices=DatasetSource.choices,
        db_index=True,
    )

    target_completed = models.BooleanField(
        db_index=True,
        help_text=(
            "True only when the donation reached confirmed "
            "COMPLETED status."
        ),
    )

    approved_at = models.DateTimeField()

    outcome_at = models.DateTimeField()

    failure_reason = models.TextField(
        blank=True,
    )

    feature_snapshot = models.JSONField(
        default=dict,
        help_text=(
            "Immutable features captured at recommendation "
            "time."
        ),
    )

    baseline_version = models.CharField(
        max_length=50,
    )

    baseline_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    recommendation_timestamp = (
        models.DateTimeField()
    )

    collected_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "match_training_records"
        ordering = ["approved_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    outcome_at__gte=models.F(
                        "approved_at"
                    )
                ),
                name="train_outcome_after_approval",
            ),
            models.CheckConstraint(
                condition=(
                    Q(baseline_score__isnull=True)
                    | (
                        Q(baseline_score__gte=0)
                        & Q(baseline_score__lte=100)
                    )
                ),
                name="train_score_0_100",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "dataset_source",
                    "target_completed",
                ],
                name="train_source_target_idx",
            ),
            models.Index(
                fields=["approved_at"],
                name="train_approved_idx",
            ),
        ]

    def __str__(self):
        outcome = (
            "completed"
            if self.target_completed
            else "not completed"
        )

        return (
            f"{self.donation_request_id}: "
            f"{outcome}"
        )