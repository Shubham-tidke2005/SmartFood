from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import (
    csrf_protect,
    ensure_csrf_cookie,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ContactVerificationSerializer,
    EmailSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    ProfileSerializer,
    RegistrationSerializer,
    UserReadSerializer,
)
from .services import (
    CONTACT_VERIFICATION_SALT,
    revoke_all_refresh_tokens,
    send_contact_verification_email,
    send_password_reset_email,
)


User = get_user_model()


def set_refresh_cookie(response, refresh_token):
    max_age = int(
        settings.SIMPLE_JWT[
            "REFRESH_TOKEN_LIFETIME"
        ].total_seconds()
    )

    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=str(refresh_token),
        max_age=max_age,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        httponly=settings.JWT_REFRESH_COOKIE_HTTP_ONLY,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


def delete_refresh_cookie(response):
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


@method_decorator(
    ensure_csrf_cookie,
    name="dispatch",
)
class CsrfTokenView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "csrf_token": get_token(request),
            }
        )


class RegistrationView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        return Response(
            {
                "message": (
                    "Registration successful. "
                    "Check the development console for "
                    "the contact-verification link."
                ),
                "user": UserReadSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class LoginView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "access": str(refresh.access_token),
                "token_type": "Bearer",
                "expires_in": int(
                    settings.SIMPLE_JWT[
                        "ACCESS_TOKEN_LIFETIME"
                    ].total_seconds()
                ),
                "user": UserReadSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

        set_refresh_cookie(
            response=response,
            refresh_token=refresh,
        )

        return response


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class RefreshAccessTokenView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE_NAME
        )

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token is missing.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(
            data={
                "refresh": refresh_token,
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        response = Response(
            {
                "access": (
                    serializer.validated_data["access"]
                ),
                "token_type": "Bearer",
                "expires_in": int(
                    settings.SIMPLE_JWT[
                        "ACCESS_TOKEN_LIFETIME"
                    ].total_seconds()
                ),
            }
        )

        rotated_refresh = (
            serializer.validated_data.get("refresh")
        )

        if rotated_refresh:
            set_refresh_cookie(
                response=response,
                refresh_token=rotated_refresh,
            )

        return response


@method_decorator(
    csrf_protect,
    name="dispatch",
)
class LogoutView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE_NAME
        )

        if refresh_token:
            try:
                RefreshToken(
                    refresh_token
                ).blacklist()
            except TokenError:
                pass

        response = Response(
            status=status.HTTP_204_NO_CONTENT
        )

        delete_refresh_cookie(response)

        return response


class PasswordResetRequestView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = EmailSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).first()

        if user:
            send_password_reset_email(user)

        return Response(
            {
                "message": (
                    "If the account exists, password-reset "
                    "instructions have been sent."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data[
            "new_password"
        ]

        try:
            user_id = force_str(
                urlsafe_base64_decode(uid)
            )

            user = User.objects.get(
                pk=user_id,
                is_active=True,
            )

        except (
            ValueError,
            TypeError,
            OverflowError,
            User.DoesNotExist,
        ):
            return Response(
                {
                    "detail": (
                        "The password-reset token is invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(
            user,
            token,
        ):
            return Response(
                {
                    "detail": (
                        "The password-reset token is invalid "
                        "or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(
                password=new_password,
                user=user,
            )

        except DjangoValidationError as error:
            return Response(
                {
                    "new_password": list(error.messages),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.auth_version += 1

        user.save(
            update_fields=[
                "password",
                "auth_version",
            ]
        )

        revoke_all_refresh_tokens(user)

        return Response(
            {
                "message": (
                    "Password reset successful. "
                    "Please log in again."
                )
            }
        )


class ContactVerificationConfirmView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = ContactVerificationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        token = serializer.validated_data["token"]

        try:
            payload = signing.loads(
                token,
                salt=CONTACT_VERIFICATION_SALT,
                max_age=60 * 60 * 24,
            )

            user = User.objects.get(
                pk=payload["user_id"],
                email__iexact=payload["email"],
                is_active=True,
            )

        except (
            signing.BadSignature,
            signing.SignatureExpired,
            KeyError,
            User.DoesNotExist,
        ):
            return Response(
                {
                    "detail": (
                        "The contact-verification token is "
                        "invalid or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.contact_verified_at is None:
            user.contact_verified_at = timezone.now()

            user.save(
                update_fields=[
                    "contact_verified_at",
                ]
            )

        return Response(
            {
                "message": (
                    "Contact verified successfully. "
                    "Participant approval may still be required."
                )
            }
        )


class ContactVerificationResendView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = EmailSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
            contact_verified_at__isnull=True,
        ).first()

        if user:
            send_contact_verification_email(user)

        return Response(
            {
                "message": (
                    "If an unverified account exists, "
                    "verification instructions have been sent."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MyProfileView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request):
        serializer = ProfileSerializer(
            request.user
        )

        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(serializer.data)