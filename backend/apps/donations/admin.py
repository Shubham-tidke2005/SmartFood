from django.contrib import admin

from .models import (
    Donation,
    DonationImage,
    DonationRequest,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)


class DonationImageInline(admin.TabularInline):
    model = DonationImage
    extra = 0

    fields = [
        "original_name",
        "mime_type",
        "size_bytes",
        "position",
        "created_at",
    ]

    readonly_fields = fields


@admin.register(DonationRevision)
class DonationRevisionAdmin(admin.ModelAdmin):
    list_display = [
        "food_name",
        "donation",
        "number",
        "category",
        "quantity",
        "unit",
        "is_current",
        "pickup_deadline",
    ]

    list_filter = [
        "is_current",
        "category",
        "unit",
    ]

    search_fields = [
        "food_name",
        "donation__donor__email",
    ]

    inlines = [
        DonationImageInline,
    ]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "donor",
        "status",
        "custody_hold",
        "published_at",
        "closed_at",
    ]

    list_filter = [
        "status",
        "custody_hold",
    ]

    search_fields = [
        "donor__email",
        "donor__display_name",
    ]

    readonly_fields = [
        "id",
        "donor",
        "status",
        "custody_hold",
        "published_at",
        "closed_at",
        "created_at",
        "updated_at",
    ]


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "active",
        "requires_preparation_time",
        "requires_use_by",
    ]

    list_filter = [
        "active",
        "requires_preparation_time",
        "requires_use_by",
    ]

    search_fields = [
        "name",
        "code",
    ]


@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "donation",
        "receiver",
        "status",
        "proposed_mode",
        "created_at",
        "expires_at",
    ]

    list_filter = [
        "status",
        "proposed_mode",
    ]

    search_fields = [
        "receiver__email",
        "donation__donor__email",
    ]

    readonly_fields = [
        "id",
        "donation",
        "receiver",
        "requested_revision",
        "status",
        "proposed_mode",
        "expires_at",
        "decided_at",
        "reason",
        "created_at",
        "updated_at",
    ]


@admin.register(DonationStatusHistory)
class DonationStatusHistoryAdmin(
    admin.ModelAdmin
):
    list_display = [
        "donation",
        "event_type",
        "from_status",
        "to_status",
        "actor",
        "created_at",
    ]

    list_filter = [
        "event_type",
        "to_status",
    ]

    readonly_fields = [
        "id",
        "donation",
        "actor",
        "event_type",
        "from_status",
        "to_status",
        "reason",
        "created_at",
    ]