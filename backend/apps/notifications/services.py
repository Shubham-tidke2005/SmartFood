import logging

from .models import Notification


logger = logging.getLogger(__name__)


def create_notification(
    *,
    recipient_id,
    notification_type,
    title,
    message,
    data=None,
    deduplication_key=None,
    queue_on_failure=True,
    raise_errors=False,
):
    try:
        if deduplication_key:
            notification, _ = (
                Notification.objects.get_or_create(
                    deduplication_key=(
                        deduplication_key
                    ),
                    defaults={
                        "recipient_id": recipient_id,
                        "notification_type": (
                            notification_type
                        ),
                        "title": title,
                        "message": message,
                        "data": data or {},
                    },
                )
            )

            return notification

        return Notification.objects.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
        )

    except Exception:
        logger.exception(
            "Could not create notification for user %s.",
            recipient_id,
        )

        if queue_on_failure:
            try:
                from apps.operations.services import (
                    enqueue_notification_retry,
                )

                enqueue_notification_retry(
                    recipient_id=recipient_id,
                    notification_type=(
                        notification_type
                    ),
                    title=title,
                    message=message,
                    data=data,
                    deduplication_key=(
                        deduplication_key
                    ),
                )

            except Exception:
                logger.exception(
                    "Could not queue failed notification."
                )

        if raise_errors:
            raise

        return None


def create_notifications(events):
    results = []

    for event in events:
        results.append(
            create_notification(**event)
        )

    return results