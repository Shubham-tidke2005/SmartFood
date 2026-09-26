import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class OperationalIssue(models.Model):
    class IssueType(models.TextChoices):
        MISSED_PICKUP = (
            "MISSED_PICKUP",
            "Missed pickup",
        )
        VOLUNTEER_CANCELLATION = (
            "VOLUNTEER_CANCELLATION",
            "Volunteer cancellation",
        )
        TRANSPORT_FAILURE = (
            "TRANSPORT_FAILURE",
            "Transport failure",
        )
        DELIVERY_REJECTED = (
            "DELIVERY_REJECTED",
            "Delivery rejected",
        )
        RECEIPT_OVERDUE = (
            "RECEIPT_OVERDUE",
            "Receipt confirmation overdue",
        )
        ACCOUNT_SUSPENDED = (
            "ACCOUNT_SUSPENDED",
            "Participant account suspended",
        )

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    deduplication_key = models.CharField(
        max_length=255,
        unique=True,
    )

    issue_type = models.CharField(
        max_length=40,
        choices=IssueType.choices,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    donation = models.ForeignKey(
        "donations.Donation",
        on_delete=models.PROTECT,
        related_name="operational_issues",
        null=True,
        blank=True,
    )

    donation_request = models.ForeignKey(
        "donations.DonationRequest",
        on_delete=models.PROTECT,
        related_name="operational_issues",
        null=True,
        blank=True,
    )

    volunteer_task = models.ForeignKey(
        "logistics.VolunteerTask",
        on_delete=models.PROTECT,
        related_name="operational_issues",
        null=True,
        blank=True,
    )

    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operational_issues",
        null=True,
        blank=True,
    )

    summary = models.CharField(
        max_length=255,
    )

    details = models.JSONField(
        default=dict,
        blank=True,
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "operational_issues"
        ordering = ["-detected_at"]

        indexes = [
            models.Index(
                fields=["status", "issue_type"],
                name="op_issue_status_type_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.issue_type}: "
            f"{self.summary}"
        )


class BackgroundJob(models.Model):
    class JobType(models.TextChoices):
        SEND_NOTIFICATION = (
            "SEND_NOTIFICATION",
            "Send notification",
        )

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    deduplication_key = models.CharField(
        max_length=255,
        unique=True,
    )

    job_type = models.CharField(
        max_length=40,
        choices=JobType.choices,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    payload = models.JSONField(
        default=dict,
    )

    run_after = models.DateTimeField(
        db_index=True,
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    max_attempts = models.PositiveSmallIntegerField(
        default=5,
    )

    last_error = models.TextField(
        blank=True,
    )

    locked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "background_jobs"
        ordering = ["run_after", "created_at"]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "run_after",
                ],
                name="background_job_due_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(max_attempts__gt=0),
                name=(
                    "background_job_attempt_limit_positive"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.job_type}: "
            f"{self.status}"
        )