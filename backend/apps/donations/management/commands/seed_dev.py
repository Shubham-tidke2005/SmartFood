from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.donations.models import (
    Donation,
    DonationRevision,
    FoodCategory,
)


User = get_user_model()


class Command(BaseCommand):
    help = "Create synthetic SmartFood development data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            required=True,
            help="Password for all synthetic development accounts.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "The seed_dev command can only run when DEBUG=True."
            )

        password = options["password"]

        accounts = [
            {
                "email": "donor@smartfood.local",
                "display_name": "Green Kitchen",
                "role": User.Role.DONOR,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "receiver@smartfood.local",
                "display_name": "Helping Hands NGO",
                "role": User.Role.RECEIVER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "volunteer@smartfood.local",
                "display_name": "Development Volunteer",
                "role": User.Role.VOLUNTEER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "admin@smartfood.local",
                "display_name": "SmartFood Administrator",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        created_users = {}

        for account in accounts:
            email = account["email"]

            user, created = User.objects.update_or_create(
                email=email,
                defaults={
                    "display_name": account["display_name"],
                    "role": account["role"],
                    "verification_status": (
                        User.VerificationStatus.VERIFIED
                    ),
                    "contact_verified_at": timezone.now(),
                    "is_active": True,
                    "is_staff": account["is_staff"],
                    "is_superuser": account["is_superuser"],
                },
            )

            user.set_password(password)
            user.save(update_fields=["password"])

            created_users[email] = user

            action = "Created" if created else "Updated"

            self.stdout.write(
                f"{action} user: {email}"
            )

        prepared_meals, _ = FoodCategory.objects.update_or_create(
            code="prepared-meals",
            defaults={
                "name": "Prepared Meals",
                "active": True,
            },
        )

        bakery, _ = FoodCategory.objects.update_or_create(
            code="bakery",
            defaults={
                "name": "Bakery Items",
                "active": True,
            },
        )

        donor = created_users["donor@smartfood.local"]
        now = timezone.now()

        donation_one, _ = Donation.objects.get_or_create(
            donor=donor,
            status=Donation.Status.AVAILABLE,
            revisions__food_name="Vegetable Rice Meals",
        )

        DonationRevision.objects.update_or_create(
            donation=donation_one,
            number=1,
            defaults={
                "is_current": True,
                "food_name": "Vegetable Rice Meals",
                "category": prepared_meals,
                "quantity": "25.000",
                "unit": DonationRevision.Unit.PORTION,
                "description": (
                    "Freshly prepared vegetarian rice meals."
                ),
                "storage_condition": "Keep covered and collect promptly.",
                "pickup_address": (
                    "Synthetic address, Pune, Maharashtra"
                ),
                "pickup_starts_at": now + timedelta(hours=1),
                "pickup_deadline": now + timedelta(hours=5),
                "proposed_by": donor,
            },
        )

        donation_two, _ = Donation.objects.get_or_create(
            donor=donor,
            status=Donation.Status.AVAILABLE,
            revisions__food_name="Bread Packages",
        )

        DonationRevision.objects.update_or_create(
            donation=donation_two,
            number=1,
            defaults={
                "is_current": True,
                "food_name": "Bread Packages",
                "category": bakery,
                "quantity": "12.000",
                "unit": DonationRevision.Unit.PACKAGE,
                "description": (
                    "Synthetic bakery donation for development testing."
                ),
                "storage_condition": "Store in a dry place.",
                "pickup_address": (
                    "Synthetic bakery address, Pune, Maharashtra"
                ),
                "pickup_starts_at": now + timedelta(hours=2),
                "pickup_deadline": now + timedelta(hours=8),
                "proposed_by": donor,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic development data is ready."
            )
        )