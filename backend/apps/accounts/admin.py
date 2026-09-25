from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]

    list_display = [
        "email",
        "display_name",
        "role",
        "verification_status",
        "is_active",
        "is_staff",
    ]

    list_filter = [
        "role",
        "verification_status",
        "is_active",
        "is_staff",
    ]

    search_fields = [
        "email",
        "display_name",
        "mobile",
    ]

    readonly_fields = [
        "id",
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Account",
            {
                "fields": [
                    "id",
                    "email",
                    "password",
                ],
            },
        ),
        (
            "Personal information",
            {
                "fields": [
                    "display_name",
                    "mobile",
                ],
            },
        ),
        (
            "SmartFood role",
            {
                "fields": [
                    "role",
                    "verification_status",
                    "contact_verified_at",
                    "auth_version",
                ],
            },
        ),
        (
            "Django permissions",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ],
            },
        ),
        (
            "Important dates",
            {
                "fields": [
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]

    add_fieldsets = [
        (
            "Create user",
            {
                "classes": ["wide"],
                "fields": [
                    "email",
                    "display_name",
                    "mobile",
                    "role",
                    "verification_status",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ],
            },
        ),
    ]