from django.contrib import admin

from .models import Donation, DonationRevision, FoodCategory


class DonationRevisionInline(admin.TabularInline):
    model = DonationRevision
    extra = 0

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "donor",
        "status",
        "custody_hold",
        "published_at",
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
        "published_at",
        "created_at",
        "updated_at",
    ]

    inlines = [
        DonationRevisionInline,
    ]


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "active",
    ]

    list_filter = [
        "active",
    ]

    search_fields = [
        "name",
        "code",
    ]