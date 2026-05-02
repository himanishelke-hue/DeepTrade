"""
Django settings for core project — Production-Ready
"""
from pathlib import Path
import os
import secrets
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────────────
# Fix 1: Use SECRET_KEY env var, then SESSION_SECRET (Replit), then persist a
#        stable generated key to .secret_key so restarts never corrupt sessions.
SECRET_KEY = config('SECRET_KEY', default=None) or config('SESSION_SECRET', default=None)
if not SECRET_KEY:
    _key_file = BASE_DIR / '.secret_key'
    if _key_file.exists():
        SECRET_KEY = _key_file.read_text().strip()
    else:
        SECRET_KEY = secrets.token_hex(50)
        try:
            _key_file.write_text(SECRET_KEY)
        except OSError:
            pass   # read-only FS; key will be regenerated on restart

DEBUG = config('DEBUG', default=True, cast=bool)

# Allow all Replit preview hosts + standard local hosts
_raw_hosts = config('ALLOWED_HOSTS', default='')
if _raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*'] if DEBUG else ['127.0.0.1', 'localhost']

# ─── Applications ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'app',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]
SITE_ID = 1
SITE_DOMAIN = config('SITE_DOMAIN', default='localhost:8000')

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.HealthCheckMiddleware',
    'core.middleware.APIErrorMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
_db_url = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
DATABASES = {'default': dj_database_url.parse(_db_url, conn_max_age=600)}

# ─── Caching — Fix 2: in-memory cache so yfinance results are reused ─────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'deeptrade-cache',
    }
}
YFINANCE_CACHE_SECONDS = 300   # 5 minutes — avoids hammering Yahoo Finance on every request

# ─── Password Validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ─── Static Files ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'app' / 'static',
    BASE_DIR / 'static',
]
# Use simple (non-manifest) storage so a missing file never breaks startup
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Auth / Allauth ───────────────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# ─── Google OAuth (optional) ──────────────────────────────────────────────────
# Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env to enable Google login.
# Without them the Google button is automatically hidden — no crash, no admin setup needed.
_google_id     = config('GOOGLE_CLIENT_ID',     default='')
_google_secret = config('GOOGLE_CLIENT_SECRET', default='')
if _google_id and _google_secret:
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'APP': {
                'client_id': _google_id,
                'secret':    _google_secret,
                'key':       '',
            },
            'SCOPE':       ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
        }
    }

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── CSRF ─────────────────────────────────────────────────────────────────────
_csrf_raw = config('CSRF_TRUSTED_ORIGINS', default='http://127.0.0.1:8000,http://localhost:8000')
CSRF_TRUSTED_ORIGINS = [h.strip() for h in _csrf_raw.split(',') if h.strip()]

# ─── External API Keys ────────────────────────────────────────────────────────
GROQ_API_KEY = config('GROQ_API_KEY', default='')

# ─── Security Headers (production only) ──────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{levelname}] {asctime} {module}: {message}', 'style': '{'},
        'simple':  {'format': '[{levelname}] {message}', 'style': '{'},
    },
    'filters': {
        'suppress_session_corruption': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda r: 'Session data corrupted' not in r.getMessage(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['suppress_session_corruption'],
        },
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django':         {'handlers': ['console'], 'level': 'INFO',  'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
        'app':            {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        # ── Silence yfinance internal spam ────────────────────────────────────
        # These loggers flood the console with rate-limit errors and connection
        # pool warnings that are already handled gracefully in views.py.
        'yfinance':              {'handlers': ['console'], 'level': 'CRITICAL', 'propagate': False},
        'peewee':                {'handlers': ['console'], 'level': 'CRITICAL', 'propagate': False},
        'urllib3.connectionpool':{'handlers': ['console'], 'level': 'ERROR',    'propagate': False},
    },
}
