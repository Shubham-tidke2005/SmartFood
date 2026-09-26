import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q

from .storage import private_verification_storage


def verification_document_path(instance, filename):
    extension = Path(filename).suffix.lower()

    return (
        f"verifications/"
        f"{instance.submission.user_id}/"
        f"{uuid.uuid4().hex}{extension}"
    )


class VerificationSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_submissions",
    )

    attempt = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    submitted_details = models.JSONField(
        default=dict,
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_verifications",
        null=True,
        blank=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "verification_submissions"

        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "attempt",
                ],
                name="unique_verification_attempt",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="PENDING"),
                name="one_pending_verification_per_user",
            ),
            models.CheckConstraint(
                condition=Q(attempt__gt=0),
                name="verification_attempt_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"attempt {self.attempt} — "
            f"{self.status}"
        )


class VerificationDocument(models.Model):
    class DocumentType(models.TextChoices):
        IDENTITY = "IDENTITY", "Identity document"
        ORGANIZATION_REGISTRATION = (
            "ORGANIZATION_REGISTRATION",
            "Organization registration",
        )
        ADDRESS_PROOF = "ADDRESS_PROOF", "Address proof"
        OTHER = "OTHER", "Other document"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    submission = models.ForeignKey(
        VerificationSubmission,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=40,
        choices=DocumentType.choices,
    )

    file = models.FileField(
        storage=private_verification_storage,
        upload_to=verification_document_path,
        max_length=500,
    )

    original_name = models.CharField(
        max_length=255,
    )

    mime_type = models.CharField(
        max_length=100,
    )

    size_bytes = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "verification_documents"
        ordering = ["created_at"]

    def __str__(self):
        return self.original_name


class VerificationHistory(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"
        REOPENED = "REOPENED", "Reopened"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_history",
    )

    submission = models.ForeignKey(
        VerificationSubmission,
        on_delete=models.PROTECT,
        related_name="history",
        null=True,
        blank=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_actions",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    from_status = models.CharField(
        max_length=20,
        blank=True,
    )

    to_status = models.CharField(
        max_length=20,
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "verification_history"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"{self.action} — "
            f"{self.created_at}"
        )