"""LOCAL VALIDATION ONLY: source ZIPs did not contain config/settings.py.

This is not a replacement for SmartFood production settings. SQLite cannot
validate select_for_update; PostgreSQL concurrency tests explicitly skip here.
"""
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = "isolated-step27-test-harness-only-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
ROOT_URLCONF = "_step27_urls"
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    *[f"apps.{name}" for name in (
        "accounts", "donations", "receivers", "logistics", "recommendations",
        "notifications", "analytics", "moderation", "operations",
    )],
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Asia/Kolkata"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "test@example.test"
FRONTEND_URL = "http://127.0.0.1:5173"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
_media = TemporaryDirectory(prefix="smartfood-step27-harness-")
MEDIA_ROOT = Path(_media.name) / "public"
PRIVATE_MEDIA_ROOT = Path(_media.name) / "private"
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
MAX_DONATION_IMAGE_SIZE = 5 * 1024 * 1024
MAX_DONATION_IMAGES = 5
MAX_VERIFICATION_FILE_SIZE = 5 * 1024 * 1024
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}
JWT_REFRESH_COOKIE_NAME = "sf_refresh"
JWT_REFRESH_COOKIE_PATH = "/api/auth/"
JWT_REFRESH_COOKIE_SECURE = False
JWT_REFRESH_COOKIE_HTTP_ONLY = True
JWT_REFRESH_COOKIE_SAMESITE = "Lax"
SMARTFOOD_RECOMMENDATIONS = {
    "BASELINE_VERSION": "baseline-2.0",
    "BASELINE_WEIGHTS": {"distance": 0.3, "quantity_match": 0.3,
                         "availability_overlap": 0.2, "transport_readiness": 0.2},
}
SMARTFOOD_ML = {"ENABLED": False}

