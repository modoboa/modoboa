"""
Django settings for {{ name }} project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from logging.handlers import SysLogHandler
import os
import environ
{% if devmode %}

from modoboa.core.dev_settings import *  # noqa
{% endif %}

env = environ.Env()
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ secret_key }}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = {{ devmode }}

ALLOWED_HOSTS = [
    '{{ allowed_host }}',
]

SITE_ID = 1

# A list of all the people who get code error notifications. When DEBUG=False
# and a view raises an exception, Django will email these people with the full
# exception information.
# See https://docs.djangoproject.com/en/dev/ref/settings/#admins
#ADMINS = [('Administrator', 'admin@example.net')]

# The email address that error messages come from, such as those sent to ADMINS
#SERVER_EMAIL = 'webmaster@example.net'

# Security settings

X_FRAME_OPTIONS = "SAMEORIGIN"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'reversion',
    'ckeditor',
    'ckeditor_uploader',
    'oauth2_provider',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'phonenumber_field',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'django_rename_app',
    'django_rq',
{% if devmode %}    'djangobower',{% endif %}
)

# A dedicated place to register Modoboa applications
# Do not delete it.
# Do not change the order.
MODOBOA_APPS = (
    'modoboa',
    'modoboa.core',
    'modoboa.lib',
    'modoboa.admin',
    'modoboa.transport',
    'modoboa.relaydomains',
    'modoboa.limits',
    'modoboa.parameters',
    'modoboa.dnstools',
    'modoboa.policyd',
    'modoboa.maillog',
    'modoboa.pdfcredentials',
    'modoboa.dmarc',
    'modoboa.imap_migration',
    'modoboa.postfix_autoreply',
    'modoboa.sievefilters',
    'modoboa.contacts',
    'modoboa.calendars',
    # Modoboa extensions here.
{% for extension in extensions %}    '{{ extension }}',
{% endfor %}
)

INSTALLED_APPS += MODOBOA_APPS

AUTH_USER_MODEL = 'core.User'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'x_forwarded_for.middleware.XForwardedForMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'modoboa.core.middleware.LocalConfigMiddleware',
    'modoboa.lib.middleware.AjaxLoginRedirect',
    'modoboa.lib.middleware.CommonExceptionCatcher',
    'modoboa.lib.middleware.RequestCatcherMiddleware',
)

AUTHENTICATION_BACKENDS = (
    #'modoboa.lib.authbackends.LDAPBackend',
    #'modoboa.lib.authbackends.SMTPBackend',
    'django.contrib.auth.backends.ModelBackend',
    'modoboa.imap_migration.auth_backends.IMAPBackend',
)

# SMTP authentication
#AUTH_SMTP_SERVER_ADDRESS = 'localhost'
#AUTH_SMTP_SERVER_PORT = 25
#AUTH_SMTP_SECURED_MODE = None  # 'ssl' or 'starttls' are accepted


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'modoboa.core.context_processors.top_notifications',
                'modoboa.core.context_processors.new_admin_url',
            ],
            'debug': {{ devmode }},
        },
    },
]

ROOT_URLCONF = '{{ name }}.urls'

WSGI_APPLICATION = '{{ name }}.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    {% for conn in db_connections.values %}{{ conn|safe }}{% endfor %}
}

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = '{{ lang }}'

TIME_ZONE = '{{ timezone }}'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/sitestatic/'
STATIC_ROOT = os.path.join(BASE_DIR, 'sitestatic')
STATICFILES_DIRS = (
    '{{ bower_components_dir }}',
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# oAuth2 settings

OAUTH2_PROVIDER = {
    'OIDC_ENABLED': True,
    'OIDC_RP_INITIATED_LOGOUT_ENABLED': True,
    'OIDC_RP_INITIATED_LOGOUT_ALWAYS_PROMPT': True,
    'OIDC_RSA_PRIVATE_KEY': env.str('OIDC_RSA_PRIVATE_KEY', multiline=True),
    'SCOPES': {
        'openid': 'OpenID Connect scope',
        'read': 'Read scope',
        'write': 'Write scope',
        'introspection': 'Introspect token scope',
    },
    'DEFAULT_SCOPES': ['openid', 'read', 'write'],
}

# If CORS fail, you might want to try to set it to True
#CORS_ORIGIN_ALLOW_ALL = False

# Rest framework settings

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'user': '300/minute',
        'ddos': '5/second',
        'ddos_lesser': '200/minute',
        'login': '10/minute',
        'password_recovery_request': '12/hour',
        'password_recovery_totp_check': '25/hour',
        'password_recovery_apply': '25/hour'
    },
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',

}

# Uncomment if you need a custom sub url for new_admin interface
# NEW_ADMIN_URL = 'new-admin'

SPECTACULAR_SETTINGS = {
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'TITLE': 'Modoboa API',
    'VERSION': None,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
}

# Modoboa settings

#MODOBOA_CUSTOM_LOGO = os.path.join(MEDIA_URL, "custom_logo.png")

# Path to Dovecot binaries in case of a non-standard installation
#DOVECOT_LOOKUP_PATH = ('/path/to/dovecot', )
#DOVEADM_LOOKUP_PATH = ('/path/to/doveadm', )

# List of supported schemes if doveadm is not available, given by: doveadm pw -l
#DOVECOT_SUPPORTED_SCHEMES = 'SHA512-CRYPT SHA256-CRYPT'

# DOVECOT_USER = 'vmail'

MODOBOA_API_URL = 'https://api.modoboa.org/1/'

DISABLE_DASHBOARD_EXTERNAL_QUERIES = False

PID_FILE_STORAGE_PATH = '/var/run'

# REDIS

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_QUOTA_DB = 0
REDIS_URL = 'redis://{}:{}/{}'.format(REDIS_HOST, REDIS_PORT, REDIS_QUOTA_DB)
# To use unix socket, use this scheme instead
# REDIS_HOST must point to the socket path
# REDIS_URL = 'unix://{}?db={}'.format(REDIS_HOST, REDIS_QUOTA_DB)

# RQ

RQ_QUEUES = {
    'dkim': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_QUOTA_DB,
        'URL': REDIS_URL,
    },
    'modoboa': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_QUOTA_DB,
        'URL': REDIS_URL,
    },
}

# CACHE

CACHES = {
    "default": {
        "BACKEND": 'django.core.cache.backends.redis.RedisCache',
        "LOCATION": REDIS_URL
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'modoboa.core.password_validation.ComplexityValidator',
        'OPTIONS': {
            'upper': 1,
            'lower': 1,
            'digits': 1,
            'specials': 0
        }
    },
]

# 2FA

OTP_TOTP_ISSUER = "{{ allowed_host }}"

# CKeditor

CKEDITOR_UPLOAD_PATH = "uploads/"

CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_RESTRICT_BY_USER = True

CKEDITOR_BROWSE_SHOW_DIRS = True

CKEDITOR_ALLOW_NONIMAGE_FILES = False

CKEDITOR_CONFIGS = {
    'default': {
        'allowedContent': True,
        'toolbar': 'Modoboa',
        'width': None,
        'toolbar_Modoboa': [
            ['Bold', 'Italic', 'Underline'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['BidiLtr', 'BidiRtl', 'Language'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Undo', 'Redo'],
            ['Link', 'Unlink', 'Anchor', '-', 'Smiley'],
            ['TextColor', 'BGColor', '-', 'Source'],
            ['Font', 'FontSize'],
            ['Image', ],
            ['SpellChecker']
        ],
    },
}

# Logging configuration

LOGGING = {
    'version': 1,
    'formatters': {
        'syslog': {
            'format': '%(name)s: %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail-admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        },
        'syslog-auth': {
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_AUTH,
            'formatter': 'syslog',
            'address': '/dev/log'
        },
        'syslog-mail': {
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_MAIL,
            'formatter': 'syslog'
        },
        'modoboa': {
            'class': 'modoboa.core.loggers.SQLHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['mail-admins'],
            'level': 'ERROR',
            'propagate': False
        },
        'modoboa.auth': {
            'handlers': ['syslog-auth', 'modoboa'],
            'level': 'INFO',
            'propagate': False
        },
        'modoboa.admin': {
            'handlers': ['modoboa'],
            'level': 'INFO',
            'propagate': False
        },
        'modoboa.policyd': {
            'handlers': ['syslog-mail'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

SILENCED_SYSTEM_CHECKS = [
    "security.W019",  # modoboa uses iframes to display e-mails
    "ckeditor.W001",  # CKEditor 4.22.1 warning
]

PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'

# Load settings from extensions
{% for extension in extra_settings %}
try:
    from {{ extension }} import settings as {{ extension }}_settings
    {{ extension }}_settings.apply(globals())
except AttributeError:
    from {{ extension }}.settings import *  # noqa
{% endfor %}
