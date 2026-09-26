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
        REQUEST_EXPIRED = (
            "REQUEST_EXPIRED",
            "Request expired",
        )
        ARRANGEMENT_CANCELLED = (
            "ARRANGEMENT_CANCELLED",
            "Arrangement cancelled",
        )
        DONATION_CANCELLED = (
            "DONATION_CANCELLED",
            "Donation cancelled",
        )
        DONATION_EXPIRED = (
            "DONATION_EXPIRED",
            "Donation expired",
        )
        HANDOVER_CONFIRMED = (
            "HANDOVER_CONFIRMED",
            "Handover confirmed",
        )
        DELIVERY_RECORDED = (
            "DELIVERY_RECORDED",
            "Delivery recorded",
        )
        RECEIPT_CONFIRMED = (
            "RECEIPT_CONFIRMED",
            "Receipt confirmed",
        )
        RECEIPT_REJECTED = (
            "RECEIPT_REJECTED",
            "Receipt rejected",
        )
        RECEIPT_REMINDER = (
            "RECEIPT_REMINDER",
            "Receipt confirmation reminder",
        )
        PICKUP_REMINDER = (
            "PICKUP_REMINDER",
            "Pickup reminder",
        )
        PICKUP_OVERDUE = (
            "PICKUP_OVERDUE",
            "Pickup overdue",
        )
        VOLUNTEER_TASK_ASSIGNED = (
            "VOLUNTEER_TASK_ASSIGNED",
            "Volunteer task assigned",
        )
        VOLUNTEER_PICKUP = (
            "VOLUNTEER_PICKUP",
            "Volunteer pickup",
        )
        VOLUNTEER_DELIVERY = (
            "VOLUNTEER_DELIVERY",
            "Volunteer delivery",
        )
        VOLUNTEER_TASK_FAILED = (
            "VOLUNTEER_TASK_FAILED",
            "Volunteer task failed",
        )
        VOLUNTEER_TASK_REASSIGNED = (
            "VOLUNTEER_TASK_REASSIGNED",
            "Volunteer task reassigned",
        )
        ACCOUNT_SUSPENDED = (
            "ACCOUNT_SUSPENDED",
            "Account suspended",
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

    deduplication_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=160,
    )

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