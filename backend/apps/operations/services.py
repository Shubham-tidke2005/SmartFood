import logging
import uuid

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationRevision,
)
from apps.donations.request_services import (
    release_requirement_capacity,
)
from apps.donations.services import (
    expire_donation_if_required,
    record_donation_history,
)
from apps.logistics.models import (
    DeliveryRecord,
    HandoverRecord,
    ReceiptConfirmation,
    VolunteerFailureReport,
    VolunteerProfile,
    VolunteerTask,
    VolunteerTaskHistory,
)
from apps.logistics.volunteer_services import (
    record_task_history,
    refresh_volunteer_status,
)
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import (
    BackgroundJob,
    OperationalIssue,
)


logger = logging.getLogger(__name__)


def create_operational_issue(
    *,
    deduplication_key,
    issue_type,
    summary,
    donation_id=None,
    donation_request_id=None,
    volunteer_task_id=None,
    affected_user_id=None,
    details=None,
):
    return OperationalIssue.objects.get_or_create(
        deduplication_key=deduplication_key,
        defaults={
            "issue_type": issue_type,
            "summary": summary,
            "donation_id": donation_id,
            "donation_request_id": (
                donation_request_id
            ),
            "volunteer_task_id": volunteer_task_id,
            "affected_user_id": affected_user_id,
            "details": details or {},
        },
    )


def enqueue_notification(
    *,
    deduplication_key,
    recipient_id,
    notification_type,
    title,
    message,
    data=None,
    run_after=None,
    max_attempts=5,
):
    run_after = run_after or timezone.now()

    payload = {
        "recipient_id": str(recipient_id),
        "notification_type": str(notification_type),
        "title": title,
        "message": message,
        "data": data or {},
        "deduplication_key": deduplication_key,
    }

    return BackgroundJob.objects.get_or_create(
        deduplication_key=deduplication_key,
        defaults={
            "job_type": (
                BackgroundJob.JobType.SEND_NOTIFICATION
            ),
            "status": BackgroundJob.Status.PENDING,
            "payload": payload,
            "run_after": run_after,
            "max_attempts": max_attempts,
        },
    )


def enqueue_notification_retry(
    *,
    recipient_id,
    notification_type,
    title,
    message,
    data=None,
    deduplication_key=None,
):
    key = (
        deduplication_key
        or f"notification-retry:{uuid.uuid4()}"
    )

    return enqueue_notification(
        deduplication_key=key,
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        message=message,
        data=data,
    )


def _current_revision(donation):
    return (
        DonationRevision.objects
        .filter(
            donation=donation,
            is_current=True,
        )
        .select_related("category")
        .first()
    )


def expire_available_donations(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()
    processed = 0

    donation_ids = list(
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

    for donation_id in donation_ids:
        with transaction.atomic():
            donation = (
                Donation.objects
                .select_for_update()
                .select_related("donor")
                .get(pk=donation_id)
            )

            expired = expire_donation_if_required(
                donation,
                current_time=current_time,
            )

            if not expired:
                continue

            pending_requests = list(
                DonationRequest.objects
                .select_for_update()
                .select_related("receiver")
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.PENDING
                    ),
                )
            )

            for donation_request in pending_requests:
                donation_request.status = (
                    DonationRequest.Status.EXPIRED
                )
                donation_request.decided_at = current_time
                donation_request.reason = (
                    "Donation expired before the request "
                    "was approved."
                )

                donation_request.save(
                    update_fields=[
                        "status",
                        "decided_at",
                        "reason",
                        "updated_at",
                    ]
                )

                enqueue_notification(
                    deduplication_key=(
                        f"donation-expired-request:"
                        f"{donation_request.id}"
                    ),
                    recipient_id=(
                        donation_request.receiver_id
                    ),
                    notification_type=(
                        Notification.Type.DONATION_EXPIRED
                    ),
                    title="Donation expired",
                    message=(
                        "The donation expired before your "
                        "request could be approved."
                    ),
                    data={
                        "donation_id": str(donation.id),
                        "request_id": str(
                            donation_request.id
                        ),
                    },
                )

            enqueue_notification(
                deduplication_key=(
                    f"donation-expired-donor:{donation.id}"
                ),
                recipient_id=donation.donor_id,
                notification_type=(
                    Notification.Type.DONATION_EXPIRED
                ),
                title="Donation expired",
                message=(
                    "The pickup deadline passed before "
                    "the donation was collected."
                ),
                data={
                    "donation_id": str(donation.id),
                },
            )

            processed += 1

    return processed


def expire_unanswered_requests(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()
    processed = 0

    request_ids = list(
        DonationRequest.objects.filter(
            status=DonationRequest.Status.PENDING,
            expires_at__lte=current_time,
        ).values_list("id", flat=True)
    )

    for request_id in request_ids:
        with transaction.atomic():
            donation_request = (
                DonationRequest.objects
                .select_for_update()
                .select_related(
                    "donation",
                    "donation__donor",
                    "receiver",
                )
                .get(pk=request_id)
            )

            if (
                donation_request.status
                != DonationRequest.Status.PENDING
                or donation_request.expires_at
                > current_time
            ):
                continue

            donation_request.status = (
                DonationRequest.Status.EXPIRED
            )
            donation_request.decided_at = current_time
            donation_request.reason = (
                "The donor did not answer before the "
                "request deadline."
            )

            donation_request.save(
                update_fields=[
                    "status",
                    "decided_at",
                    "reason",
                    "updated_at",
                ]
            )

            enqueue_notification(
                deduplication_key=(
                    f"request-expired:"
                    f"{donation_request.id}"
                ),
                recipient_id=(
                    donation_request.receiver_id
                ),
                notification_type=(
                    Notification.Type.REQUEST_EXPIRED
                ),
                title="Donation request expired",
                message=(
                    "The donor did not respond before "
                    "the request deadline."
                ),
                data={
                    "donation_id": str(
                        donation_request.donation_id
                    ),
                    "request_id": str(
                        donation_request.id
                    ),
                },
            )

            processed += 1

    return processed


def process_missed_pickups(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()
    processed = 0

    donation_ids = list(
        Donation.objects.filter(
            status=Donation.Status.RESERVED,
            revisions__is_current=True,
            revisions__pickup_deadline__lte=(
                current_time
            ),
        )
        .values_list("id", flat=True)
        .distinct()
    )

    for donation_id in donation_ids:
        with transaction.atomic():
            donation = (
                Donation.objects
                .select_for_update()
                .select_related("donor")
                .get(pk=donation_id)
            )

            revision = _current_revision(donation)

            if (
                donation.status
                != Donation.Status.RESERVED
                or revision is None
                or revision.pickup_deadline
                > current_time
            ):
                continue

            if HandoverRecord.objects.filter(
                donation=donation
            ).exists():
                continue

            approved_request = (
                DonationRequest.objects
                .select_for_update()
                .select_related("receiver")
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.APPROVED
                    ),
                )
                .first()
            )

            receiver_id = None

            if approved_request is not None:
                receiver_id = (
                    approved_request.receiver_id
                )

                release_requirement_capacity(
                    donation_request=approved_request
                )

                approved_request.status = (
                    DonationRequest.Status.CANCELLED
                )
                approved_request.decided_at = current_time
                approved_request.reason = (
                    "Pickup was not completed before "
                    "the deadline."
                )

                approved_request.save(
                    update_fields=[
                        "status",
                        "decided_at",
                        "reason",
                        "updated_at",
                    ]
                )

            volunteer_task = (
                VolunteerTask.objects
                .select_for_update()
                .filter(donation=donation)
                .first()
            )

            volunteer_id = None

            if volunteer_task is not None:
                volunteer_id = (
                    volunteer_task.assigned_volunteer_id
                )
                previous_task_status = (
                    volunteer_task.status
                )

                if volunteer_task.status not in {
                    VolunteerTask.Status.COMPLETED,
                    VolunteerTask.Status.CANCELLED,
                    VolunteerTask.Status.FAILED,
                }:
                    volunteer_task.status = (
                        VolunteerTask.Status.FAILED
                    )
                    volunteer_task.closed_at = current_time

                    volunteer_task.save(
                        update_fields=[
                            "status",
                            "closed_at",
                            "updated_at",
                        ]
                    )

                    record_task_history(
                        task=volunteer_task,
                        actor=None,
                        event_type="MISSED_PICKUP",
                        from_status=previous_task_status,
                        to_status=(
                            VolunteerTask.Status.FAILED
                        ),
                        reason=(
                            "Pickup deadline passed before "
                            "handover."
                        ),
                    )

            previous_status = donation.status

            donation.status = Donation.Status.EXPIRED
            donation.closed_at = current_time

            donation.save(
                update_fields=[
                    "status",
                    "closed_at",
                    "updated_at",
                ]
            )

            record_donation_history(
                donation=donation,
                actor=None,
                event_type="MISSED_PICKUP",
                from_status=previous_status,
                to_status=Donation.Status.EXPIRED,
                reason=(
                    "Pickup deadline passed before "
                    "handover."
                ),
            )

            create_operational_issue(
                deduplication_key=(
                    f"missed-pickup:{donation.id}"
                ),
                issue_type=(
                    OperationalIssue.IssueType
                    .MISSED_PICKUP
                ),
                summary=(
                    "Pickup was not completed before "
                    "the deadline."
                ),
                donation_id=donation.id,
                donation_request_id=(
                    approved_request.id
                    if approved_request
                    else None
                ),
                volunteer_task_id=(
                    volunteer_task.id
                    if volunteer_task
                    else None
                ),
                details={
                    "pickup_deadline": (
                        revision.pickup_deadline.isoformat()
                    ),
                },
            )

            recipients = {
                donation.donor_id,
                receiver_id,
                volunteer_id,
            }

            for recipient_id in recipients:
                if recipient_id is None:
                    continue

                enqueue_notification(
                    deduplication_key=(
                        f"missed-pickup:"
                        f"{donation.id}:"
                        f"{recipient_id}"
                    ),
                    recipient_id=recipient_id,
                    notification_type=(
                        Notification.Type.PICKUP_OVERDUE
                    ),
                    title="Pickup deadline missed",
                    message=(
                        "The donation was not collected "
                        "before its pickup deadline."
                    ),
                    data={
                        "donation_id": str(donation.id),
                    },
                )

            if volunteer_id is not None:
                profile = (
                    VolunteerProfile.objects
                    .select_for_update()
                    .filter(user_id=volunteer_id)
                    .first()
                )

                if profile is not None:
                    refresh_volunteer_status(profile)

            processed += 1

    return processed


def identify_receipt_overdue(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()

    grace_hours = getattr(
        settings,
        "SMARTFOOD_RECEIPT_GRACE_HOURS",
        6,
    )

    hold_hours = getattr(
        settings,
        "SMARTFOOD_RECEIPT_HOLD_HOURS",
        24,
    )

    grace_cutoff = (
        current_time - timedelta(hours=grace_hours)
    )
    hold_cutoff = (
        current_time - timedelta(hours=hold_hours)
    )

    processed = 0

    donation_ids = list(
        Donation.objects.filter(
            status__in=[
                Donation.Status.PICKED_UP,
                Donation.Status.DELIVERED,
            ],
            receipt_confirmation__isnull=True,
        ).values_list("id", flat=True)
    )

    for donation_id in donation_ids:
        with transaction.atomic():
            donation = (
                Donation.objects
                .select_for_update()
                .select_related("donor")
                .get(pk=donation_id)
            )

            if ReceiptConfirmation.objects.filter(
                donation=donation
            ).exists():
                continue

            approved_request = (
                DonationRequest.objects
                .select_related("receiver")
                .filter(
                    donation=donation,
                    status=(
                        DonationRequest.Status.APPROVED
                    ),
                )
                .first()
            )

            if approved_request is None:
                continue

            delivery = (
                DeliveryRecord.objects
                .filter(donation=donation)
                .first()
            )

            handover = (
                HandoverRecord.objects
                .filter(donation=donation)
                .first()
            )

            reference_time = None

            if delivery is not None:
                reference_time = delivery.delivered_at
            elif handover is not None:
                reference_time = handover.handed_over_at

            if (
                reference_time is None
                or reference_time > grace_cutoff
            ):
                continue

            _, created = create_operational_issue(
                deduplication_key=(
                    f"receipt-overdue:{donation.id}"
                ),
                issue_type=(
                    OperationalIssue.IssueType
                    .RECEIPT_OVERDUE
                ),
                summary=(
                    "Receiver confirmation has not been "
                    "recorded."
                ),
                donation_id=donation.id,
                donation_request_id=(
                    approved_request.id
                ),
                affected_user_id=(
                    approved_request.receiver_id
                ),
                details={
                    "reference_time": (
                        reference_time.isoformat()
                    ),
                },
            )

            reminder_date = (
                timezone.localdate().isoformat()
            )

            enqueue_notification(
                deduplication_key=(
                    f"receipt-reminder:"
                    f"{donation.id}:"
                    f"{reminder_date}"
                ),
                recipient_id=(
                    approved_request.receiver_id
                ),
                notification_type=(
                    Notification.Type.RECEIPT_REMINDER
                ),
                title="Confirm donation receipt",
                message=(
                    "Please confirm the quantity received "
                    "or report a delivery problem."
                ),
                data={
                    "donation_id": str(donation.id),
                    "request_id": str(
                        approved_request.id
                    ),
                },
            )

            if (
                reference_time <= hold_cutoff
                and not donation.custody_hold
            ):
                donation.custody_hold = True
                donation.save(
                    update_fields=[
                        "custody_hold",
                        "updated_at",
                    ]
                )

            if created:
                processed += 1

    return processed


def identify_recorded_failures(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()
    processed = 0

    failure_reports = (
        VolunteerFailureReport.objects
        .select_related(
            "task",
            "task__donation",
            "task__donation_request",
            "volunteer",
        )
        .filter(
            created_at__gte=(
                current_time - timedelta(days=30)
            )
        )
    )

    for report in failure_reports:
        _, created = create_operational_issue(
            deduplication_key=(
                f"transport-failure:{report.id}"
            ),
            issue_type=(
                OperationalIssue.IssueType
                .TRANSPORT_FAILURE
            ),
            summary="Volunteer reported a transport failure.",
            donation_id=report.task.donation_id,
            donation_request_id=(
                report.task.donation_request_id
            ),
            volunteer_task_id=report.task_id,
            affected_user_id=report.volunteer_id,
            details={
                "stage": report.stage,
                "reason": report.reason,
                "reassign_requested": (
                    report.reassign_requested
                ),
            },
        )

        if created:
            processed += 1

    rejected_receipts = (
        ReceiptConfirmation.objects
        .select_related(
            "donation",
            "donation_request",
            "confirmed_by",
        )
        .filter(
            accepted_quantity=0,
            created_at__gte=(
                current_time - timedelta(days=30)
            ),
        )
    )

    for receipt in rejected_receipts:
        _, created = create_operational_issue(
            deduplication_key=(
                f"delivery-rejected:{receipt.id}"
            ),
            issue_type=(
                OperationalIssue.IssueType
                .DELIVERY_REJECTED
            ),
            summary=(
                "Receiver rejected the delivered quantity."
            ),
            donation_id=receipt.donation_id,
            donation_request_id=(
                receipt.donation_request_id
            ),
            affected_user_id=receipt.confirmed_by_id,
            details={
                "discrepancy_type": (
                    receipt.discrepancy_type
                ),
                "notes": receipt.discrepancy_notes,
            },
        )

        if created:
            processed += 1

    cancellation_histories = (
        VolunteerTaskHistory.objects
        .select_related(
            "task",
            "task__donation",
            "task__donation_request",
            "actor",
        )
        .filter(
            event_type__icontains="CANCEL",
            created_at__gte=(
                current_time - timedelta(days=30)
            ),
        )
    )

    for history in cancellation_histories:
        _, created = create_operational_issue(
            deduplication_key=(
                f"volunteer-cancellation:{history.id}"
            ),
            issue_type=(
                OperationalIssue.IssueType
                .VOLUNTEER_CANCELLATION
            ),
            summary=(
                "A volunteer assignment was cancelled."
            ),
            donation_id=history.task.donation_id,
            donation_request_id=(
                history.task.donation_request_id
            ),
            volunteer_task_id=history.task_id,
            affected_user_id=history.actor_id,
            details={
                "reason": history.reason,
                "from_status": history.from_status,
                "to_status": history.to_status,
            },
        )

        if created:
            processed += 1

    return processed


def identify_suspended_accounts():
    processed = 0

    suspended_users = User.objects.filter(
        is_active=True,
        verification_status=(
            User.VerificationStatus.SUSPENDED
        ),
    )

    for user in suspended_users:
        donation_ids = set()

        if user.role == User.Role.DONOR:
            donation_ids.update(
                Donation.objects.filter(
                    donor=user,
                    status__in=[
                        Donation.Status.AVAILABLE,
                        Donation.Status.RESERVED,
                        Donation.Status.PICKED_UP,
                        Donation.Status.DELIVERED,
                    ],
                ).values_list("id", flat=True)
            )

        if user.role == User.Role.RECEIVER:
            donation_ids.update(
                DonationRequest.objects.filter(
                    receiver=user,
                    status=(
                        DonationRequest.Status.APPROVED
                    ),
                    donation__status__in=[
                        Donation.Status.RESERVED,
                        Donation.Status.PICKED_UP,
                        Donation.Status.DELIVERED,
                    ],
                ).values_list(
                    "donation_id",
                    flat=True,
                )
            )

        if user.role == User.Role.VOLUNTEER:
            volunteer_profile = (
                VolunteerProfile.objects
                .filter(user=user)
                .first()
            )

            if volunteer_profile is not None:
                volunteer_profile.operational = False
                volunteer_profile.availability_status = (
                    VolunteerProfile
                    .AvailabilityStatus.UNAVAILABLE
                )
                volunteer_profile.save(
                    update_fields=[
                        "operational",
                        "availability_status",
                        "updated_at",
                    ]
                )

            donation_ids.update(
                VolunteerTask.objects.filter(
                    assigned_volunteer=user,
                    status__in=[
                        VolunteerTask.Status.ASSIGNED,
                        VolunteerTask.Status
                        .ARRIVED_AT_DONOR,
                        VolunteerTask.Status.PICKED_UP,
                        VolunteerTask.Status
                        .ARRIVED_AT_RECEIVER,
                    ],
                ).values_list(
                    "donation_id",
                    flat=True,
                )
            )

        for donation_id in donation_ids:
            with transaction.atomic():
                donation = (
                    Donation.objects
                    .select_for_update()
                    .get(pk=donation_id)
                )

                if not donation.custody_hold:
                    donation.custody_hold = True
                    donation.save(
                        update_fields=[
                            "custody_hold",
                            "updated_at",
                        ]
                    )

                _, created = create_operational_issue(
                    deduplication_key=(
                        f"suspended-account:"
                        f"{user.id}:"
                        f"{donation.id}"
                    ),
                    issue_type=(
                        OperationalIssue.IssueType
                        .ACCOUNT_SUSPENDED
                    ),
                    summary=(
                        "A suspended participant is part "
                        "of an active transaction."
                    ),
                    donation_id=donation.id,
                    affected_user_id=user.id,
                    details={
                        "role": user.role,
                    },
                )

                if created:
                    processed += 1

    return processed


def create_due_reminders(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()

    reminder_minutes = getattr(
        settings,
        "SMARTFOOD_PICKUP_REMINDER_MINUTES",
        60,
    )

    reminder_end = (
        current_time
        + timedelta(minutes=reminder_minutes)
    )

    processed = 0

    donation_ids = list(
        Donation.objects.filter(
            status=Donation.Status.RESERVED,
            revisions__is_current=True,
            revisions__pickup_deadline__gt=(
                current_time
            ),
            revisions__pickup_deadline__lte=(
                reminder_end
            ),
        )
        .values_list("id", flat=True)
        .distinct()
    )

    for donation_id in donation_ids:
        donation = (
            Donation.objects
            .select_related("donor")
            .get(pk=donation_id)
        )

        approved_request = (
            DonationRequest.objects
            .filter(
                donation=donation,
                status=DonationRequest.Status.APPROVED,
            )
            .first()
        )

        recipients = {donation.donor_id}

        if approved_request is not None:
            recipients.add(
                approved_request.receiver_id
            )

        volunteer_task = (
            VolunteerTask.objects
            .filter(
                donation=donation,
                assigned_volunteer__isnull=False,
            )
            .first()
        )

        if volunteer_task is not None:
            recipients.add(
                volunteer_task.assigned_volunteer_id
            )

        for recipient_id in recipients:
            _, created = enqueue_notification(
                deduplication_key=(
                    f"pickup-reminder:"
                    f"{donation.id}:"
                    f"{recipient_id}"
                ),
                recipient_id=recipient_id,
                notification_type=(
                    Notification.Type.PICKUP_REMINDER
                ),
                title="Pickup deadline approaching",
                message=(
                    "The donation pickup deadline is "
                    "approaching."
                ),
                data={
                    "donation_id": str(donation.id),
                },
            )

            if created:
                processed += 1

    return processed


def recover_stuck_jobs(
    *,
    current_time=None,
):
    current_time = current_time or timezone.now()

    timeout_minutes = getattr(
        settings,
        "SMARTFOOD_JOB_LOCK_TIMEOUT_MINUTES",
        10,
    )

    cutoff = (
        current_time
        - timedelta(minutes=timeout_minutes)
    )

    return BackgroundJob.objects.filter(
        status=BackgroundJob.Status.PROCESSING,
        locked_at__lt=cutoff,
        attempts__lt=models_max_attempts_expression(),
    ).update(
        status=BackgroundJob.Status.PENDING,
        locked_at=None,
        run_after=current_time,
    )


def models_max_attempts_expression():
    from django.db.models import F

    return F("max_attempts")


def process_notification_jobs(
    *,
    batch_size=100,
    current_time=None,
):
    current_time = current_time or timezone.now()
    completed = 0
    failed = 0

    recover_stuck_jobs(
        current_time=current_time
    )

    for _ in range(batch_size):
        with transaction.atomic():
            job = (
                BackgroundJob.objects
                .select_for_update(skip_locked=True)
                .filter(
                    status=BackgroundJob.Status.PENDING,
                    run_after__lte=timezone.now(),
                    attempts__lt=(
                        models_max_attempts_expression()
                    ),
                )
                .order_by(
                    "run_after",
                    "created_at",
                )
                .first()
            )

            if job is None:
                break

            job.status = BackgroundJob.Status.PROCESSING
            job.attempts += 1
            job.locked_at = timezone.now()

            job.save(
                update_fields=[
                    "status",
                    "attempts",
                    "locked_at",
                    "updated_at",
                ]
            )

            job_id = job.id
            payload = dict(job.payload)
            attempt_number = job.attempts
            max_attempts = job.max_attempts

        try:
            if (
                job.job_type
                == BackgroundJob.JobType
                .SEND_NOTIFICATION
            ):
                create_notification(
                    recipient_id=payload["recipient_id"],
                    notification_type=(
                        payload["notification_type"]
                    ),
                    title=payload["title"],
                    message=payload["message"],
                    data=payload.get("data", {}),
                    deduplication_key=(
                        payload["deduplication_key"]
                    ),
                    queue_on_failure=False,
                    raise_errors=True,
                )
            else:
                raise ValueError(
                    f"Unsupported job type: "
                    f"{job.job_type}"
                )

        except Exception as exc:
            logger.exception(
                "Background job %s failed.",
                job_id,
            )

            with transaction.atomic():
                locked_job = (
                    BackgroundJob.objects
                    .select_for_update()
                    .get(pk=job_id)
                )

                locked_job.last_error = str(exc)[:4000]
                locked_job.locked_at = None

                if attempt_number >= max_attempts:
                    locked_job.status = (
                        BackgroundJob.Status.FAILED
                    )
                else:
                    delay_minutes = min(
                        2 ** attempt_number,
                        60,
                    )

                    locked_job.status = (
                        BackgroundJob.Status.PENDING
                    )
                    locked_job.run_after = (
                        timezone.now()
                        + timedelta(
                            minutes=delay_minutes
                        )
                    )

                locked_job.save(
                    update_fields=[
                        "status",
                        "run_after",
                        "last_error",
                        "locked_at",
                        "updated_at",
                    ]
                )

            failed += 1
            continue

        with transaction.atomic():
            locked_job = (
                BackgroundJob.objects
                .select_for_update()
                .get(pk=job_id)
            )

            locked_job.status = (
                BackgroundJob.Status.SUCCEEDED
            )
            locked_job.completed_at = timezone.now()
            locked_job.locked_at = None
            locked_job.last_error = ""

            locked_job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "locked_at",
                    "last_error",
                    "updated_at",
                ]
            )

        completed += 1

    return {
        "completed": completed,
        "failed": failed,
    }


def run_background_cycle(
    *,
    batch_size=100,
):
    current_time = timezone.now()

    results = {
        "donations_expired": (
            expire_available_donations(
                current_time=current_time
            )
        ),
        "requests_expired": (
            expire_unanswered_requests(
                current_time=current_time
            )
        ),
        "missed_pickups": (
            process_missed_pickups(
                current_time=current_time
            )
        ),
        "receipt_overdue": (
            identify_receipt_overdue(
                current_time=current_time
            )
        ),
        "recorded_failures": (
            identify_recorded_failures(
                current_time=current_time
            )
        ),
        "suspended_accounts": (
            identify_suspended_accounts()
        ),
        "reminders_created": (
            create_due_reminders(
                current_time=current_time
            )
        ),
    }

    results["notification_jobs"] = (
        process_notification_jobs(
            batch_size=batch_size,
            current_time=current_time,
        )
    )

    return results