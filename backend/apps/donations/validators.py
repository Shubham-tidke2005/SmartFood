from pathlib import Path

from django.conf import settings
from PIL import Image
from rest_framework import serializers


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def validate_donation_image(uploaded_file):
    if uploaded_file.size <= 0:
        raise serializers.ValidationError(
            "The uploaded image is empty."
        )

    if (
        uploaded_file.size
        > settings.MAX_DONATION_IMAGE_SIZE
    ):
        raise serializers.ValidationError(
            "Each image must be 5 MB or smaller."
        )

    content_type = getattr(
        uploaded_file,
        "content_type",
        "",
    ).lower()

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    allowed_extensions = ALLOWED_IMAGE_TYPES.get(
        content_type
    )

    if (
        allowed_extensions is None
        or extension not in allowed_extensions
    ):
        raise serializers.ValidationError(
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image.verify()

    except Exception as error:
        raise serializers.ValidationError(
            "The uploaded image is invalid or corrupted."
        ) from error

    finally:
        uploaded_file.seek(0)

    return uploaded_file