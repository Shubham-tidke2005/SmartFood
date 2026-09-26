from datetime import timedelta
from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")


SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool(
    "DJANGO_DEBUG",
    default=False,
)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "127.0.0.1",
        "localhost",
    ],
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",

    "apps.accounts.apps.AccountsConfig",
    "apps.donations.apps.DonationsConfig",
    "apps.receivers.apps.ReceiversConfig",
    "apps.logistics.apps.LogisticsConfig",
    "apps.recommendations.apps.RecommendationsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.moderation.apps.ModerationConfig",
    "apps.operations.apps.OperationsConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django."
            "DjangoTemplates"
        ),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                (
                    "django.template.context_processors."
                    "request"
                ),
                (
                    "django.contrib.auth.context_processors."
                    "auth"
                ),
                (
                    "django.contrib.messages.context_processors."
                    "messages"
                ),
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console."
        "EmailBackend"
    ),
)

DEFAULT_FROM_EMAIL = (
    "SmartFood <noreply@smartfood.local>"
)

FRONTEND_URL = env(
    "FRONTEND_URL",
    default="http://127.0.0.1:5173",
)


DATABASES = {
    "default": {
        "ENGINE": (
            "django.db.backends.postgresql"
        ),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env(
            "DB_HOST",
            default="localhost",
        ),
        "PORT": env(
            "DB_PORT",
            default="5432",
        ),
        "CONN_MAX_AGE": 60,
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


AUTH_USER_MODEL = "accounts.User"


LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

PRIVATE_MEDIA_ROOT = (
    BASE_DIR / "private_media"
)


MAX_DONATION_IMAGE_SIZE = (
    5 * 1024 * 1024
)

MAX_DONATION_IMAGES = 5


# React development servers
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

CORS_ALLOW_CREDENTIALS = True


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        (
            "rest_framework_simplejwt."
            "authentication.JWTAuthentication"
        ),
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        (
            "rest_framework.permissions."
            "IsAuthenticated"
        ),
    ],
    "DEFAULT_RENDERER_CLASSES": [
        (
            "rest_framework.renderers."
            "JSONRenderer"
        ),
        (
            "rest_framework.renderers."
            "BrowsableAPIRenderer"
        ),
    ],
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": (
        timedelta(minutes=5)
    ),
    "REFRESH_TOKEN_LIFETIME": (
        timedelta(days=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


JWT_REFRESH_COOKIE_NAME = "sf_refresh"
JWT_REFRESH_COOKIE_PATH = "/api/auth/"
JWT_REFRESH_COOKIE_SECURE = not DEBUG
JWT_REFRESH_COOKIE_HTTP_ONLY = True
JWT_REFRESH_COOKIE_SAMESITE = "Lax"


SMARTFOOD_PICKUP_REMINDER_MINUTES = env.int(
    "SMARTFOOD_PICKUP_REMINDER_MINUTES",
    default=60,
)

SMARTFOOD_RECEIPT_GRACE_HOURS = env.int(
    "SMARTFOOD_RECEIPT_GRACE_HOURS",
    default=6,
)

SMARTFOOD_RECEIPT_HOLD_HOURS = env.int(
    "SMARTFOOD_RECEIPT_HOLD_HOURS",
    default=24,
)

SMARTFOOD_JOB_LOCK_TIMEOUT_MINUTES = env.int(
    "SMARTFOOD_JOB_LOCK_TIMEOUT_MINUTES",
    default=10,
)


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)