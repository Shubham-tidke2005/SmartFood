from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.donations.models import (
    Donation,
    DonationRevision,
    DonationStatusHistory,
    FoodCategory,
)


User = get_user_model()


class Command(BaseCommand):
    help = "Create development users, categories, and sample donations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default="SmartFoodDev@123",
            help="Password assigned to all development accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        self.stdout.write("")
        self.stdout.write("Creating development accounts...")

        donor = self.create_user(
            email="donor@smartfood.local",
            password=password,
            role=User.Role.DONOR,
            first_name="Development",
            last_name="Donor",
        )

        self.create_user(
            email="receiver@smartfood.local",
            password=password,
            role=User.Role.RECEIVER,
            first_name="Development",
            last_name="Receiver",
        )

        self.create_user(
            email="volunteer@smartfood.local",
            password=password,
            role=User.Role.VOLUNTEER,
            first_name="Development",
            last_name="Volunteer",
        )

        self.create_user(
            email="admin@smartfood.local",
            password=password,
            role=User.Role.ADMIN,
            first_name="Development",
            last_name="Administrator",
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write("")
        self.stdout.write("Creating food categories...")

        prepared_meals = self.create_category(
            code="prepared-meals",
            name="Prepared Meals",
            requires_preparation_time=True,
            requires_use_by=True,
        )

        bakery = self.create_category(
            code="bakery",
            name="Bakery",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        fruits_vegetables = self.create_category(
            code="fruits-vegetables",
            name="Fruits and Vegetables",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        self.create_category(
            code="dairy-products",
            name="Dairy Products",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        self.create_category(
            code="packaged-food",
            name="Packaged Food",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        self.create_category(
            code="beverages",
            name="Beverages",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        self.create_category(
            code="dry-food",
            name="Dry Food",
            requires_preparation_time=False,
            requires_use_by=True,
        )

        self.stdout.write("")
        self.stdout.write("Creating sample donations...")

        now = timezone.now()

        self.create_or_update_donation(
            donor=donor,
            category=prepared_meals,
            food_name="Vegetable Rice Meals",
            quantity=Decimal("40.000"),
            unit=DonationRevision.Unit.PORTION,
            description=(
                "Freshly prepared vegetable rice packed in "
                "individual portions."
            ),
            storage_condition=(
                "Keep covered and collect as soon as possible."
            ),
            prepared_at=now - timedelta(hours=1),
            use_by_at=now + timedelta(hours=6),
            pickup_starts_at=now + timedelta(minutes=30),
            pickup_deadline=now + timedelta(hours=4),
            pickup_address=(
                "College Road, Nashik, Maharashtra"
            ),
            pickup_area="College Road",
        )

        self.create_or_update_donation(
            donor=donor,
            category=bakery,
            food_name="Assorted Bread Packages",
            quantity=Decimal("12.000"),
            unit=DonationRevision.Unit.PACKAGE,
            description=(
                "Sealed bread packages available for "
                "redistribution."
            ),
            storage_condition=(
                "Store in a cool and dry place."
            ),
            prepared_at=None,
            use_by_at=now + timedelta(days=1),
            pickup_starts_at=now + timedelta(hours=1),
            pickup_deadline=now + timedelta(hours=8),
            pickup_address=(
                "Gangapur Road, Nashik, Maharashtra"
            ),
            pickup_area="Gangapur Road",
        )

        self.create_or_update_donation(
            donor=donor,
            category=fruits_vegetables,
            food_name="Fresh Bananas",
            quantity=Decimal("18.500"),
            unit=DonationRevision.Unit.KG,
            description=(
                "Ripe bananas suitable for immediate "
                "distribution."
            ),
            storage_condition="Store at room temperature.",
            prepared_at=None,
            use_by_at=now + timedelta(days=2),
            pickup_starts_at=now + timedelta(hours=2),
            pickup_deadline=now + timedelta(hours=12),
            pickup_address=(
                "Panchavati, Nashik, Maharashtra"
            ),
            pickup_area="Panchavati",
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Development data created successfully."
            )
        )

        self.stdout.write("")
        self.stdout.write("Development accounts:")
        self.stdout.write(
            f"  Donor:     donor@smartfood.local / {password}"
        )
        self.stdout.write(
            f"  Receiver:  receiver@smartfood.local / {password}"
        )
        self.stdout.write(
            f"  Volunteer: volunteer@smartfood.local / {password}"
        )
        self.stdout.write(
            f"  Admin:     admin@smartfood.local / {password}"
        )
        self.stdout.write("")

    def create_user(
        self,
        *,
        email,
        password,
        role,
        first_name,
        last_name,
        is_staff=False,
        is_superuser=False,
    ):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )

        user.role = role
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.contact_verified_at = timezone.now()
        user.verification_status = (
            User.VerificationStatus.VERIFIED
        )

        user.set_password(password)

        user.save(
            update_fields=[
                "role",
                "first_name",
                "last_name",
                "is_active",
                "is_staff",
                "is_superuser",
                "contact_verified_at",
                "verification_status",
                "password",
            ]
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action}: {user.email}")

        return user

    def create_category(
        self,
        *,
        code,
        name,
        requires_preparation_time,
        requires_use_by,
    ):
        category, created = FoodCategory.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "active": True,
                "requires_preparation_time": (
                    requires_preparation_time
                ),
                "requires_use_by": requires_use_by,
            },
        )

        action = "Created" if created else "Updated"

        self.stdout.write(
            f"  {action} category: {category.name}"
        )

        return category

    def create_or_update_donation(
        self,
        *,
        donor,
        category,
        food_name,
        quantity,
        unit,
        description,
        storage_condition,
        prepared_at,
        use_by_at,
        pickup_starts_at,
        pickup_deadline,
        pickup_address,
        pickup_area,
    ):
        current_revision = (
            DonationRevision.objects
            .select_related("donation")
            .filter(
                donation__donor=donor,
                food_name=food_name,
                is_current=True,
            )
            .first()
        )

        if current_revision:
            donation = current_revision.donation

            donation.status = Donation.Status.AVAILABLE
            donation.custody_hold = False
            donation.closed_at = None

            donation.save(
                update_fields=[
                    "status",
                    "custody_hold",
                    "closed_at",
                    "updated_at",
                ]
            )

            current_revision.category = category
            current_revision.quantity = quantity
            current_revision.unit = unit
            current_revision.description = description
            current_revision.storage_condition = (
                storage_condition
            )
            current_revision.prepared_at = prepared_at
            current_revision.use_by_at = use_by_at
            current_revision.pickup_starts_at = (
                pickup_starts_at
            )
            current_revision.pickup_deadline = (
                pickup_deadline
            )
            current_revision.pickup_address = (
                pickup_address
            )
            current_revision.pickup_area = pickup_area
            current_revision.proposed_by = donor

            current_revision.save(
                update_fields=[
                    "category",
                    "quantity",
                    "unit",
                    "description",
                    "storage_condition",
                    "prepared_at",
                    "use_by_at",
                    "pickup_starts_at",
                    "pickup_deadline",
                    "pickup_address",
                    "pickup_area",
                    "proposed_by",
                    "updated_at",
                ]
            )

            self.ensure_created_history(
                donation=donation,
                actor=donor,
            )

            self.stdout.write(
                f"  Updated donation: {food_name}"
            )

            return donation

        donation = Donation.objects.create(
            donor=donor,
            status=Donation.Status.AVAILABLE,
            custody_hold=False,
        )

        DonationRevision.objects.create(
            donation=donation,
            number=1,
            is_current=True,
            food_name=food_name,
            category=category,
            quantity=quantity,
            unit=unit,
            description=description,
            storage_condition=storage_condition,
            pickup_address=pickup_address,
            pickup_starts_at=pickup_starts_at,
            pickup_deadline=pickup_deadline,
            proposed_by=donor,
            prepared_at=prepared_at,
            use_by_at=use_by_at,
            pickup_area=pickup_area,
        )

        self.ensure_created_history(
            donation=donation,
            actor=donor,
        )

        self.stdout.write(
            f"  Created donation: {food_name}"
        )

        return donation

    def ensure_created_history(
        self,
        *,
        donation,
        actor,
    ):
        created_history_exists = (
            DonationStatusHistory.objects.filter(
                donation=donation,
                event_type="CREATED",
            ).exists()
        )

        if created_history_exists:
            return

        DonationStatusHistory.objects.create(
            donation=donation,
            actor=actor,
            event_type="CREATED",
            from_status="",
            to_status=Donation.Status.AVAILABLE,
            reason="Development sample donation created.",
        )