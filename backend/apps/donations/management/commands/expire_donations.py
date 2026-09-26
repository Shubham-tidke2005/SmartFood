from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.donations.models import Donation
from apps.donations.services import (
    expire_donation_if_required,
)


class Command(BaseCommand):
    help = "Expire available donations past their deadline."

    def handle(self, *args, **options):
        current_time = timezone.now()

        donation_ids = (
            Donation.objects.filter(
                status=Donation.Status.AVAILABLE,
                revisions__is_current=True,
                revisions__pickup_deadline__lte=(
                    current_time
                ),
            )
            .values_list("id", flat=True)
            .distinct()
        )

        expired_count = 0

        for donation_id in donation_ids:
            with transaction.atomic():
                donation = (
                    Donation.objects
                    .select_for_update()
                    .get(pk=donation_id)
                )

                expired = expire_donation_if_required(
                    donation,
                    current_time=current_time,
                )

                if expired:
                    expired_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired_count} donation(s)."
            )
        )