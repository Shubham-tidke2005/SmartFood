from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


CONTACT_VERIFICATION_SALT = "smartfood.contact-verification"


def send_contact_verification_email(user):
    token = signing.dumps(
        {
            "user_id": str(user.id),
            "email": user.email,
        },
        salt=CONTACT_VERIFICATION_SALT,
        compress=True,
    )

    query_string = urlencode({"token": token})

    verification_url = (
        f"{settings.FRONTEND_URL}/verify-contact?"
        f"{query_string}"
    )

    send_mail(
        subject="Verify your SmartFood contact",
        message=(
            f"Hello {user.display_name},\n\n"
            "Verify your SmartFood contact using this link:\n"
            f"{verification_url}\n\n"
            "This link expires in 24 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(
        force_bytes(user.pk)
    )

    token = default_token_generator.make_token(user)

    query_string = urlencode(
        {
            "uid": uid,
            "token": token,
        }
    )

    reset_url = (
        f"{settings.FRONTEND_URL}/reset-password?"
        f"{query_string}"
    )

    send_mail(
        subject="Reset your SmartFood password",
        message=(
            f"Hello {user.display_name},\n\n"
            "Reset your SmartFood password using this link:\n"
            f"{reset_url}\n\n"
            "Ignore this email if you did not request a reset."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def revoke_all_refresh_tokens(user):
    outstanding_tokens = OutstandingToken.objects.filter(
        user=user
    )

    for outstanding_token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(
            token=outstanding_token
        )