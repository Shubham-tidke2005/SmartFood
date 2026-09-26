from pathlib import Path

from django.urls import reverse
from rest_framework import serializers

from .models import (
    VerificationDocument,
    VerificationHistory,
    VerificationSubmission,
)
from .validators import validate_verification_document


class VerificationDocumentReadSerializer(
    serializers.ModelSerializer
):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = VerificationDocument

        fields = [
            "id",
            "document_type",
            "original_name",
            "mime_type",
            "size_bytes",
            "download_url",
            "created_at",
        ]

        read_only_fields = fields

    def get_download_url(self, document):
        request = self.context.get("request")

        path = reverse(
            "moderation:document-download",
            kwargs={
                "document_id": document.id,
            },
        )

        if request:
            return request.build_absolute_uri(path)

        return path


class VerificationSubmissionReadSerializer(
    serializers.ModelSerializer
):
    documents = VerificationDocumentReadSerializer(
        many=True,
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    reviewer_email = serializers.SerializerMethodField()

    class Meta:
        model = VerificationSubmission

        fields = [
            "id",
            "user_email",
            "attempt",
            "status",
            "submitted_details",
            "documents",
            "reviewer_email",
            "reviewed_at",
            "reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_reviewer_email(self, submission):
        if submission.reviewer is None:
            return None

        return submission.reviewer.email


class VerificationSubmissionCreateSerializer(
    serializers.Serializer
):
    legal_name = serializers.CharField(
        max_length=160
    )

    organization_name = serializers.CharField(
        max_length=160,
        required=False,
        allow_blank=True,
    )

    registration_identifier = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    address = serializers.CharField(
        max_length=500
    )

    documents = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        max_length=5,
        write_only=True,
    )

    document_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=(
                VerificationDocument.DocumentType.choices
            )
        ),
        min_length=1,
        max_length=5,
        write_only=True,
    )

    def validate_documents(self, documents):
        for document in documents:
            validate_verification_document(document)

        return documents

    def validate(self, attrs):
        documents = attrs["documents"]
        document_types = attrs["document_types"]

        if len(documents) != len(document_types):
            raise serializers.ValidationError(
                {
                    "document_types": (
                        "Provide one document type for every "
                        "uploaded document."
                    )
                }
            )

        return attrs


class VerificationReviewSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        min_length=3,
        max_length=1000,
    )


class SuspensionSerializer(serializers.Serializer):
    reason = serializers.CharField(
        min_length=3,
        max_length=1000,
    )


class VerificationHistorySerializer(
    serializers.ModelSerializer
):
    actor_email = serializers.EmailField(
        source="actor.email",
        read_only=True,
    )

    submission_id = serializers.UUIDField(
        source="submission.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = VerificationHistory

        fields = [
            "id",
            "submission_id",
            "action",
            "from_status",
            "to_status",
            "reason",
            "actor_email",
            "created_at",
        ]

        read_only_fields = fields