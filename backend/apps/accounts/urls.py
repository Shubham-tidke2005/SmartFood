from django.urls import path

from .views import (
    ContactVerificationConfirmView,
    ContactVerificationResendView,
    CsrfTokenView,
    LoginView,
    LogoutView,
    MyProfileView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshAccessTokenView,
    RegistrationView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "auth/csrf/",
        CsrfTokenView.as_view(),
        name="csrf",
    ),
    path(
        "auth/register/",
        RegistrationView.as_view(),
        name="register",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "auth/refresh/",
        RefreshAccessTokenView.as_view(),
        name="refresh",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "auth/password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "auth/contact-verification/confirm/",
        ContactVerificationConfirmView.as_view(),
        name="contact-verification-confirm",
    ),
    path(
        "auth/contact-verification/resend/",
        ContactVerificationResendView.as_view(),
        name="contact-verification-resend",
    ),
    path(
        "profiles/me/",
        MyProfileView.as_view(),
        name="my-profile",
    ),
]