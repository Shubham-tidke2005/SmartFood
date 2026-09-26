from django.contrib import admin

from .models import (
    ReceiverAvailability,
    ReceiverPreference,
    ReceiverProfile,
    ReceiverRequirement,
    ServiceArea,
)


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "latitude",
        "longitude",
        "active",
    )

    list_filter = ("active",)
    search_fields = ("name", "code")


@admin.register(ReceiverProfile)
class ReceiverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "organization_name",
        "user",
        "service_area",
        "max_service_distance_km",
        "max_active_allocations",
        "operational",
    )

    list_filter = (
        "operational",
        "service_area",
    )

    search_fields = (
        "organization_name",
        "user__email",
    )


@admin.register(ReceiverPreference)
class ReceiverPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "receiver",
        "category",
        "active",
    )

    list_filter = (
        "active",
        "category",
    )

    search_fields = (
        "receiver__email",
        "category__name",
    )


@admin.register(ReceiverRequirement)
class ReceiverRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "receiver",
        "category",
        "unit",
        "quantity_needed",
        "quantity_reserved",
        "needed_until",
        "active",
    )

    list_filter = (
        "active",
        "category",
        "unit",
    )

    search_fields = (
        "receiver__email",
        "category__name",
    )


@admin.register(ReceiverAvailability)
class ReceiverAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "receiver",
        "weekday",
        "starts_at",
        "ends_at",
        "active",
    )

    list_filter = (
        "active",
        "weekday",
    )

    search_fields = ("receiver__email",)