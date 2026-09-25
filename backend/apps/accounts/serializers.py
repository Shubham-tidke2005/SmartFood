from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db import transaction
from rest_framework import serializers

from .models import User
from .services import send_contact_verification_email


def validate_user_password(password, user):
    try:
        validate_password(
            password=password,
            user=user,
        )
    except DjangoValidationError as error:
        raise serializers.ValidationError(
            list(error.messages)
        ) from error


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "display_name",
            "mobile",
            "role",
            "verification_status",
            "contact_verified_at",
            "is_active",
            "created_at",
        ]

        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=[
            User.Role.DONOR,
            User.Role.RECEIVER,
            User.Role.VOLUNTEER,
        ]
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User

        fields = [
            "email",
            "display_name",
            "mobile",
            "role",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return email

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.pop(
            "password_confirm",
            None,
        )

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "The passwords do not match."
                    )
                }
            )

        temporary_user = User(
            email=attrs.get("email"),
            display_name=attrs.get("display_name"),
            role=attrs.get("role"),
        )

        validate_user_password(
            password=password,
            user=temporary_user,
        )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                verification_status=(
                    User.VerificationStatus.PENDING
                ),
                **validated_data,
            )

            transaction.on_commit(
                lambda: send_contact_verification_email(
                    user
                )
            )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is disabled."
            )

        attrs["user"] = user

        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "display_name",
            "mobile",
            "role",
            "verification_status",
            "contact_verified_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
            "verification_status",
            "contact_verified_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        protected_fields = {
            "id",
            "email",
            "role",
            "verification_status",
            "contact_verified_at",
            "is_active",
            "is_staff",
            "is_superuser",
        }

        supplied_protected_fields = (
            protected_fields.intersection(
                self.initial_data.keys()
            )
        )

        if supplied_protected_fields:
            errors = {
                field: "This field cannot be changed."
                for field in supplied_protected_fields
            }

            raise serializers.ValidationError(errors)

        return attrs


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()

    token = serializers.CharField()

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        if (
            attrs["new_password"]
            != attrs["new_password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "new_password_confirm": (
                        "The passwords do not match."
                    )
                }
            )

        return attrs


class ContactVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()