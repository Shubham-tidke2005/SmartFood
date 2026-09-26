import json

from django.core.management.base import BaseCommand

from apps.operations.services import (
    create_due_reminders,
    expire_available_donations,
    expire_unanswered_requests,
    identify_receipt_overdue,
    identify_recorded_failures,
    identify_suspended_accounts,
    process_missed_pickups,
    process_notification_jobs,
    run_background_cycle,
)


class Command(BaseCommand):
    help = (
        "Processes SmartFood expiry, reminders, overdue "
        "operations and notification retries."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
        )

        parser.add_argument(
            "--scan-only",
            action="store_true",
        )

        parser.add_argument(
            "--jobs-only",
            action="store_true",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        scan_only = options["scan_only"]
        jobs_only = options["jobs_only"]

        if scan_only and jobs_only:
            self.stderr.write(
                self.style.ERROR(
                    "Use either --scan-only or "
                    "--jobs-only, not both."
                )
            )
            return

        if jobs_only:
            result = process_notification_jobs(
                batch_size=batch_size
            )

        elif scan_only:
            result = {
                "donations_expired": (
                    expire_available_donations()
                ),
                "requests_expired": (
                    expire_unanswered_requests()
                ),
                "missed_pickups": (
                    process_missed_pickups()
                ),
                "receipt_overdue": (
                    identify_receipt_overdue()
                ),
                "recorded_failures": (
                    identify_recorded_failures()
                ),
                "suspended_accounts": (
                    identify_suspended_accounts()
                ),
                "reminders_created": (
                    create_due_reminders()
                ),
            }

        else:
            result = run_background_cycle(
                batch_size=batch_size
            )

        self.stdout.write(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Background work completed."
            )
        )