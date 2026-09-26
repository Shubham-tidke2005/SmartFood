import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        REQUEST_SUBMITTED = (
            "REQUEST_SUBMITTED",
            "Request submitted",
        )
        REQUEST_WITHDRAWN = (
            "REQUEST_WITHDRAWN",
            "Request withdrawn",
        )
        REQUEST_APPROVED = (
            "REQUEST_APPROVED",
            "Request approved",
        )
        REQUEST_REJECTED = (
            "REQUEST_REJECTED",
            "Request rejected",
        )
        ARRANGEMENT_CANCELLED = (
            "ARRANGEMENT_CANCELLED",
            "Arrangement cancelled",
        )
        DONATION_CANCELLED = (
            "DONATION_CANCELLED",
            "Donation cancelled",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=40,
        choices=Type.choices,
        db_index=True,
    )

    title = models.CharField(max_length=160)
    message = models.TextField()

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.recipient.email}: "
            f"{self.notification_type}"
        )