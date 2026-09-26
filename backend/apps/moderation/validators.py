from pathlib import Path

from django.conf import settings
from PIL import Image
from rest_framework import serializers


ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
}


def validate_verification_document(uploaded_file):
    if uploaded_file.size <= 0:
        raise serializers.ValidationError(
            "The uploaded document is empty."
        )

    if (
        uploaded_file.size
        > settings.MAX_VERIFICATION_FILE_SIZE
    ):
        raise serializers.ValidationError(
            "Each document must be 5 MB or smaller."
        )

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    content_type = getattr(
        uploaded_file,
        "content_type",
        "",
    ).lower()

    allowed_extensions = ALLOWED_DOCUMENT_TYPES.get(
        content_type
    )

    if (
        allowed_extensions is None
        or extension not in allowed_extensions
    ):
        raise serializers.ValidationError(
            "Only PDF, JPG, JPEG and PNG documents are allowed."
        )

    try:
        uploaded_file.seek(0)

        if content_type == "application/pdf":
            header = uploaded_file.read(5)

            if header != b"%PDF-":
                raise serializers.ValidationError(
                    "The uploaded PDF is invalid."
                )

        else:
            image = Image.open(uploaded_file)
            image.verify()

    except serializers.ValidationError:
        raise

    except Exception as error:
        raise serializers.ValidationError(
            "The uploaded document is invalid or corrupted."
        ) from error

    finally:
        uploaded_file.seek(0)

    return uploaded_file