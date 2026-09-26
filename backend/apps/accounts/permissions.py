from rest_framework.permissions import BasePermission

from .models import User


class IsVerifiedParticipant(BasePermission):
    message = (
        "A verified and active participant account is required."
    )

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.contact_verified_at is not None
            and user.verification_status
            == User.VerificationStatus.VERIFIED
        )


class IsVerifiedDonor(IsVerifiedParticipant):
    message = (
        "Only verified donors can perform this action."
    )

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.DONOR
        )


class IsVerifiedReceiver(IsVerifiedParticipant):
    message = (
        "Only verified receivers can perform this action."
    )

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.RECEIVER
        )


class IsVerifiedVolunteer(IsVerifiedParticipant):
    message = (
        "Only verified volunteers can perform this action."
    )

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.VOLUNTEER
        )


class IsAdministrator(BasePermission):
    message = "Administrator permission is required."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == User.Role.ADMIN
            and user.is_staff
        )


class IsSelfOrAdministrator(BasePermission):
    message = (
        "You cannot access another participant's profile."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return bool(
            request.user.role == User.Role.ADMIN
            or obj.pk == request.user.pk
        )


class IsDonationOwnerOrAdministrator(BasePermission):
    message = (
        "Only the donation owner can modify this donation."
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return bool(
            request.user.role == User.Role.ADMIN
            or obj.donor_id == request.user.id
        )