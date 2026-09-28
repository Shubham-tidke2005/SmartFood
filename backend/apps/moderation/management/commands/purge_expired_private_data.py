from datetime import timedelta

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
)
from django.db import transaction
from django.utils import timezone

from apps.moderation.audit_models import (
    AuditEvent,
)
from apps.moderation.models import (
    VerificationDocument,
    VerificationSubmission,
)


class Command(BaseCommand):
    help = (
        "Remove expired audit events and private "
        "verification files according to retention policy."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Apply deletion. Without this option, "
                "the command performs a dry run."
            ),
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]

        retention = getattr(
            settings,
            "SMARTFOOD_RETENTION",
            {},
        )

        audit_days = retention.get(
            "AUDIT_EVENT_DAYS",
            2555,
        )

        verification_days = retention.get(
            "VERIFICATION_DOCUMENT_DAYS",
            730,
        )

        now = timezone.now()

        audit_cutoff = (
            now - timedelta(days=audit_days)
        )

        verification_cutoff = (
            now
            - timedelta(
                days=verification_days
            )
        )

        audit_queryset = (
            AuditEvent.objects
            .filter(
                created_at__lt=audit_cutoff
            )
            .exclude(
                action=(
                    AuditEvent.Action
                    .OUTCOME_CORRECTED
                )
            )
        )

        document_queryset = (
            VerificationDocument.objects
            .filter(
                submission__status__in=[
                    VerificationSubmission
                    .Status.APPROVED,
                    VerificationSubmission
                    .Status.REJECTED,
                ],
                submission__reviewed_at__lt=(
                    verification_cutoff
                ),
            )
        )

        audit_count = (
            audit_queryset.count()
        )
        document_count = (
            document_queryset.count()
        )

        self.stdout.write(
            f"Audit events eligible: "
            f"{audit_count}"
        )
        self.stdout.write(
            f"Verification documents eligible: "
            f"{document_count}"
        )

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run only. Use --apply "
                    "to perform deletion."
                )
            )
            return

        with transaction.atomic():
            # QuerySet deletion intentionally performs
            # retention cleanup. Individual model deletion
            # remains prohibited.
            audit_queryset.delete()

            for document in (
                document_queryset
                .select_for_update()
            ):
                if document.file:
                    document.file.delete(
                        save=False
                    )

                document.delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Retention cleanup completed."
            )
        )