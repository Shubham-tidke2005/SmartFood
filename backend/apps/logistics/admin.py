from django.contrib import admin

from .models import (
    DeliveryRecord,
    HandoverRecord,
    ReceiptConfirmation,
)


@admin.register(HandoverRecord)
class HandoverRecordAdmin(admin.ModelAdmin):
    list_display = (
        "donation",
        "donation_request",
        "confirmed_by",
        "actual_quantity",
        "unit",
        "handed_over_at",
    )

    search_fields = (
        "donation__id",
        "confirmed_by__email",
    )


@admin.register(DeliveryRecord)
class DeliveryRecordAdmin(admin.ModelAdmin):
    list_display = (
        "donation",
        "donation_request",
        "delivered_by",
        "actual_quantity",
        "unit",
        "delivered_at",
    )

    search_fields = (
        "donation__id",
        "delivered_by__email",
    )


@admin.register(ReceiptConfirmation)
class ReceiptConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        "donation",
        "donation_request",
        "confirmed_by",
        "accepted_quantity",
        "unit",
        "discrepancy_type",
        "received_at",
    )

    list_filter = (
        "discrepancy_type",
    )

    search_fields = (
        "donation__id",
        "confirmed_by__email",
    )