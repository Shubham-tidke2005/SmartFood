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
):
    try:
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

        return None


def create_notifications(events):
    for event in events:
        create_notification(**event)