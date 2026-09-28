import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        DOCUMENT_DOWNLOADED = (
            "DOCUMENT_DOWNLOADED",
            "Private document downloaded",
        )
        COMPLAINT_UPDATED = (
            "COMPLAINT_UPDATED",
            "Complaint updated",
        )
        ACCOUNT_DEACTIVATED = (
            "ACCOUNT_DEACTIVATED",
            "Account deactivated",
        )
        OUTCOME_CORRECTED = (
            "OUTCOME_CORRECTED",
            "Donation outcome corrected",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )

    action = models.CharField(
        max_length=40,
        choices=Action.choices,
        db_index=True,
    )

    target_type = models.CharField(
        max_length=80,
        db_index=True,
    )

    target_id = models.CharField(
        max_length=100,
        db_index=True,
    )

    reason = models.TextField(
        blank=True,
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "audit_events"
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "action",
                    "created_at",
                ],
                name="audit_action_created_idx",
            ),
            models.Index(
                fields=[
                    "target_type",
                    "target_id",
                ],
                name="audit_target_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Audit events cannot be modified."
            )

        return super().save(
            *args,
            **kwargs,
        )

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Audit events cannot be individually deleted."
        )

    def __str__(self):
        return (
            f"{self.action}: "
            f"{self.target_type} "
            f"{self.target_id}"
        )


class OutcomeCorrection(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    donation = models.ForeignKey(
        "donations.Donation",
        on_delete=models.PROTECT,
        related_name="outcome_corrections",
    )

    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="outcome_corrections",
    )

    old_status = models.CharField(
        max_length=20,
    )

    new_status = models.CharField(
        max_length=20,
    )

    old_closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    new_closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reason = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "outcome_corrections"
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "donation",
                    "created_at",
                ],
                name="outcome_donation_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Outcome corrections cannot be modified."
            )

        return super().save(
            *args,
            **kwargs,
        )

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Outcome corrections cannot be deleted."
        )

    def __str__(self):
        return (
            f"{self.donation_id}: "
            f"{self.old_status} → "
            f"{self.new_status}"
        )