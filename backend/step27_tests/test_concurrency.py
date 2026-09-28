"""
PostgreSQL concurrency tests for SmartFood.

Run with:

python manage.py test \
    step27_tests.test_concurrency \
    --parallel 1 \
    --verbosity 2

Each race uses separate database connections and threads.
These tests are skipped on SQLite because SQLite cannot
validate PostgreSQL row-level locking behaviour.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import (
    close_old_connections,
    connection,
    connections,
)
from django.test import (
    TransactionTestCase,
    tag,
)
from django.urls import reverse

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationStatusHistory,
)
from apps.logistics.models import (
    VolunteerTask,
    VolunteerTaskHistory,
)
from apps.receivers.models import (
    ReceiverRequirement,
)

from .factories import (
    ScenarioMixin,
    api_for,
)


@tag("concurrency")
@skipUnless(
    connection.vendor == "postgresql",
    (
        "Requires PostgreSQL row locks; "
        "SQLite is not concurrency verification."
    ),
)
class ConcurrentWorkflowTests(
    ScenarioMixin,
    TransactionTestCase,
):
    """
    Verify that row locking prevents duplicate workflow
    operations.

    TransactionTestCase is required because TestCase wraps
    every test in an outer transaction, which would prevent
    the worker threads from observing committed state
    correctly.
    """

    reset_sequences = False

    def race(self, operations):
        """
        Execute API operations at approximately the same time.

        Each operation is a tuple containing:

            (user_id, URL)

        For the tested workflows, one request must succeed
        with HTTP 200 and the competing request must be
        rejected with HTTP 409.
        """

        barrier = Barrier(
            len(operations),
        )

        def worker(operation):
            user_id, url = operation

            # Ensure this thread does not reuse a connection
            # created in another thread.
            close_old_connections()

            try:
                database = connections["default"]

                with database.cursor() as cursor:
                    cursor.execute(
                        "SET lock_timeout = '8s'"
                    )

                    cursor.execute(
                        (
                            "SET statement_timeout "
                            "= '15s'"
                        )
                    )

                user = User.objects.get(
                    pk=user_id,
                )

                client = api_for(user)

                # All workers wait here before submitting
                # their competing requests.
                barrier.wait(
                    timeout=10,
                )

                response = client.post(
                    url,
                    {},
                    format="json",
                )

                return (
                    response.status_code,
                    response.data,
                )

            finally:
                # Close the connection belonging to this
                # worker thread.
                connections["default"].close()

        try:
            with ThreadPoolExecutor(
                max_workers=len(
                    operations
                ),
            ) as executor:
                futures = [
                    executor.submit(
                        worker,
                        operation,
                    )
                    for operation in operations
                ]

                results = [
                    future.result(
                        timeout=35,
                    )
                    for future in futures
                ]

        finally:
            # Psycopg connections used around threaded test
            # client requests can be closed by Django's
            # request_finished signal.
            #
            # Reset and reconnect the main test thread so
            # subsequent test classes do not receive:
            #
            # psycopg.OperationalError:
            #     the connection is closed
            main_connection = (
                connections["default"]
            )

            main_connection.close()
            main_connection.connect()

        self.assertEqual(
            sorted(
                status_code
                for status_code, _
                in results
            ),
            [
                200,
                409,
            ],
            results,
        )

        return results

    @classmethod
    def tearDownClass(cls):
        """
        Remove any connection wrappers left by executor
        threads before Django starts another test class.
        """

        try:
            super().tearDownClass()
        finally:
            connections.close_all()

    def test_two_receivers_cannot_both_be_approved(
        self,
    ):
        donation, _ = (
            self.make_donation()
        )

        first_request = (
            self.make_request(
                donation,
                self.receiver,
            )
        )

        second_request = (
            self.make_request(
                donation,
                self.other_receiver,
            )
        )

        operations = [
            (
                self.donor.pk,
                reverse(
                    "donations:request-approve",
                    kwargs={
                        "request_id": (
                            donation_request.pk
                        ),
                    },
                ),
            )
            for donation_request in [
                first_request,
                second_request,
            ]
        ]

        self.race(operations)

        donation.refresh_from_db()

        approved_requests = (
            donation.requests.filter(
                status=(
                    DonationRequest.Status
                    .APPROVED
                ),
            )
        )

        rejected_requests = (
            donation.requests.filter(
                status=(
                    DonationRequest.Status
                    .REJECTED
                ),
            )
        )

        self.assertEqual(
            approved_requests.count(),
            1,
        )

        self.assertEqual(
            rejected_requests.count(),
            1,
        )

        approved_request = (
            approved_requests.get()
        )

        approved_requirement = (
            ReceiverRequirement.objects.get(
                receiver=(
                    approved_request.receiver
                ),
            )
        )

        self.assertEqual(
            approved_requirement
            .quantity_reserved,
            20,
        )

        if (
            approved_request.pk
            == first_request.pk
        ):
            losing_receiver = (
                second_request.receiver
            )
        else:
            losing_receiver = (
                first_request.receiver
            )

        losing_requirement = (
            ReceiverRequirement.objects.get(
                receiver=losing_receiver,
            )
        )

        self.assertEqual(
            losing_requirement
            .quantity_reserved,
            0,
        )

        self.assertEqual(
            DonationStatusHistory.objects.filter(
                donation=donation,
                event_type="REQUEST_APPROVED",
            ).count(),
            1,
        )

    def test_two_donations_cannot_overbook_same_capacity(
        self,
    ):
        first_donation, _ = (
            self.make_donation()
        )

        second_donation, _ = (
            self.make_donation(
                donor=self.other_donor,
            )
        )

        donation_requests = [
            self.make_request(
                first_donation,
                self.receiver,
            ),
            self.make_request(
                second_donation,
                self.receiver,
            ),
        ]

        operations = [
            (
                donation_request
                .donation
                .donor_id,
                reverse(
                    "donations:request-approve",
                    kwargs={
                        "request_id": (
                            donation_request.pk
                        ),
                    },
                ),
            )
            for donation_request
            in donation_requests
        ]

        self.race(operations)

        requirement = (
            ReceiverRequirement.objects.get(
                receiver=self.receiver,
            )
        )

        self.assertEqual(
            requirement.quantity_reserved,
            20,
        )

        self.assertLessEqual(
            requirement.quantity_reserved,
            requirement.quantity_needed,
        )

        self.assertEqual(
            DonationRequest.objects.filter(
                receiver=self.receiver,
                status=(
                    DonationRequest.Status
                    .APPROVED
                ),
            ).count(),
            1,
        )

        self.assertEqual(
            Donation.objects.filter(
                pk__in=[
                    first_donation.pk,
                    second_donation.pk,
                ],
                status=(
                    Donation.Status.RESERVED
                ),
            ).count(),
            1,
        )

    def test_two_volunteers_cannot_accept_one_task(
        self,
    ):
        donation, _ = (
            self.make_allocation(
                mode="VOLUNTEER_DELIVERY",
            )
        )

        task = VolunteerTask.objects.get(
            donation=donation,
        )

        second_volunteer = (
            self.make_volunteer()
        )

        url = reverse(
            "logistics:task-accept",
            kwargs={
                "task_id": task.pk,
            },
        )

        self.race(
            [
                (
                    self.volunteer.pk,
                    url,
                ),
                (
                    second_volunteer.pk,
                    url,
                ),
            ]
        )

        task.refresh_from_db()

        self.assertIn(
            task.assigned_volunteer_id,
            [
                self.volunteer.pk,
                second_volunteer.pk,
            ],
        )

        self.assertEqual(
            task.status,
            VolunteerTask.Status.ASSIGNED,
        )

        self.assertEqual(
            VolunteerTaskHistory.objects.filter(
                task=task,
                event_type="TASK_ACCEPTED",
            ).count(),
            1,
        )

    def test_one_volunteer_cannot_accept_two_active_tasks(
        self,
    ):
        first_donation, _ = (
            self.make_allocation(
                mode="VOLUNTEER_DELIVERY",
            )
        )

        second_donation, _ = (
            self.make_allocation(
                receiver=self.other_receiver,
                mode="VOLUNTEER_DELIVERY",
            )
        )

        tasks = list(
            VolunteerTask.objects.filter(
                donation__in=[
                    first_donation,
                    second_donation,
                ],
            )
        )

        self.assertEqual(
            len(tasks),
            2,
        )

        operations = [
            (
                self.volunteer.pk,
                reverse(
                    "logistics:task-accept",
                    kwargs={
                        "task_id": task.pk,
                    },
                ),
            )
            for task in tasks
        ]

        self.race(operations)

        self.assertEqual(
            VolunteerTask.objects.filter(
                assigned_volunteer=(
                    self.volunteer
                ),
                status=(
                    VolunteerTask.Status
                    .ASSIGNED
                ),
            ).count(),
            1,
        )

        self.assertEqual(
            VolunteerTask.objects.filter(
                status=(
                    VolunteerTask.Status.OPEN
                ),
                assigned_volunteer__isnull=True,
            ).count(),
            1,
        )