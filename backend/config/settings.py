from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000").rstrip("/")
DEBUG = env_bool("DJANGO_DEBUG", APP_ENV == "development")
if APP_ENV == "production" and not APP_BASE_URL.startswith("https://"):
    raise ImproperlyConfigured("APP_BASE_URL must use HTTPS in production.")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY and APP_ENV == "development":
    SECRET_KEY = "unsafe-development-key-do-not-use-in-production"
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required outside development.")
if APP_ENV == "production" and (DEBUG or SECRET_KEY.startswith("unsafe-") or len(SECRET_KEY) < 50):
    raise ImproperlyConfigured("Production requires DEBUG=false and a strong DJANGO_SECRET_KEY.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:3000")


def database_from_url(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use PostgreSQL.")
    query = parse_qs(parsed.query)
    options: dict[str, str] = {}
    if "sslmode" in query:
        options["sslmode"] = query["sslmode"][0]
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "127.0.0.1",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": 60,
        "OPTIONS": options,
    }


if env_bool("DJANGO_USE_SQLITE_FOR_TESTS"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
else:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise ImproperlyConfigured(
            "DATABASE_URL is required. SQLite is available only with "
            "DJANGO_USE_SQLITE_FOR_TESTS=true for isolated tests."
        )
    DATABASES = {"default": database_from_url(database_url)}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.content",
    "apps.locations",
    "apps.pricing",
    "apps.bookings",
    "apps.payments",
    "apps.operations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.core.middleware.CorrelationIdMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = APP_ENV != "development"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "__Host-airport_session" if APP_ENV == "production" else "airport_session"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = False
CSRF_COOKIE_SECURE = APP_ENV != "development"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = "__Host-airport_csrf" if APP_ENV == "production" else "airport_csrf"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = APP_ENV == "production"
SECURE_HSTS_SECONDS = 31536000 if APP_ENV == "production" else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = APP_ENV == "production"
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", False)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth_register": "10/hour",
        "auth_login": "20/hour",
        "auth_password_reset": "10/hour",
        "auth_token": "30/hour",
        "quote": "60/hour",
        "booking_create": "20/hour",
        "booking_access": "30/hour",
        "booking_mutation": "20/hour",
        "payment_create": "20/hour",
        "payment_status": "60/hour",
        "payment_staff": "60/hour",
        "payment_webhook": "300/minute",
        "operations_read": "120/minute",
        "operations_mutation": "30/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Airport Transfer API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.invalid")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
if APP_ENV == "production" and EMAIL_BACKEND.endswith("console.EmailBackend"):
    raise ImproperlyConfigured("The console email backend is forbidden in production.")
if APP_ENV == "production" and DEFAULT_FROM_EMAIL.endswith("@example.invalid"):
    raise ImproperlyConfigured("DEFAULT_FROM_EMAIL must be configured in production.")

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.core.logging.JsonFormatter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}
