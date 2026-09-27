import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Complaint(models.Model):
    class ComplaintType(models.TextChoices):
        DONATION = (
            "DONATION",
            "Donation",
        )
        TRANSPORT = (
            "TRANSPORT",
            "Transport",
        )
        PARTICIPANT = (
            "PARTICIPANT",
            "Participant",
        )
        VERIFICATION = (
            "VERIFICATION",
            "Verification",
        )
        OTHER = (
            "OTHER",
            "Other",
        )

    class Status(models.TextChoices):
        OPEN = (
            "OPEN",
            "Open",
        )
        IN_REVIEW = (
            "IN_REVIEW",
            "In review",
        )
        RESOLVED = (
            "RESOLVED",
            "Resolved",
        )
        REJECTED = (
            "REJECTED",
            "Rejected",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_complaints",
    )

    complaint_type = models.CharField(
        max_length=20,
        choices=ComplaintType.choices,
        default=ComplaintType.OTHER,
        db_index=True,
    )

    donation = models.ForeignKey(
        "donations.Donation",
        on_delete=models.PROTECT,
        related_name="complaints",
        null=True,
        blank=True,
    )

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_complaints",
        null=True,
        blank=True,
    )

    subject = models.CharField(
        max_length=160,
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_complaints",
        null=True,
        blank=True,
    )

    resolution = models.TextField(
        blank=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "complaints"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "created_at",
                ],
                name="complaint_status_idx",
            ),
            models.Index(
                fields=[
                    "reporter",
                    "created_at",
                ],
                name="complaint_reporter_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(reported_user__isnull=True)
                    | ~Q(
                        reported_user=models.F(
                            "reporter"
                        )
                    )
                ),
                name="complaint_not_self",
            ),
        ]

    def __str__(self):
        return (
            f"{self.subject} - "
            f"{self.status}"
        )
        
