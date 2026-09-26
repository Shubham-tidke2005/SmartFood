from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.donations.models import DonationRequest

from .volunteer_services import (
    create_task_for_approved_request,
)


@receiver(post_save, sender=DonationRequest)
def create_volunteer_task_after_approval(
    sender,
    instance,
    **kwargs,
):
    if (
        instance.status
        == DonationRequest.Status.APPROVED
        and instance.proposed_mode
        == DonationRequest.TransportMode
        .VOLUNTEER_DELIVERY
    ):
        create_task_for_approved_request(instance)