"""
Django settings for {{ name }} project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from logging.handlers import SysLogHandler

{% if devmode %}
from modoboa.core.dev_settings import *
{% endif %}

BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{{ secret_key }}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = {{ devmode }}

ALLOWED_HOSTS = [
    '{{ allowed_host }}'
]

SITE_ID = 1

# Security settings

X_FRAME_OPTIONS = "SAMEORIGIN"

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
    'rest_framework',
    'rest_framework.authtoken',
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
    'modoboa.relaydomains',
    'modoboa.limits',
    'modoboa.parameters',
    # Modoboa extensions here.
{% for extension in extensions %}    '{{ extension }}',
{% endfor %}
)

INSTALLED_APPS += MODOBOA_APPS

AUTH_USER_MODEL = 'core.User'

MIDDLEWARE_CLASSES = (
    'x_forwarded_for.middleware.XForwardedForMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'modoboa.core.middleware.LocalConfigMiddleware',
    'modoboa.lib.middleware.AjaxLoginRedirect',
    'modoboa.lib.middleware.CommonExceptionCatcher',
    'modoboa.lib.middleware.RequestCatcherMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # 'modoboa.lib.authbackends.LDAPBackend',
    # 'modoboa.lib.authbackends.SMTPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# SMTP authentication
# AUTH_SMTP_SERVER_ADDRESS = 'localhost'
# AUTH_SMTP_SERVER_PORT = 25
# AUTH_SMTP_SECURED_MODE = None  # 'ssl' or 'starttls' are accepted


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
            ],
            'debug': {{ devmode }},
        },
    },
]

ROOT_URLCONF = '{{ name }}.urls'

WSGI_APPLICATION = '{{ name }}.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    {% for conn in db_connections.values %}{{ conn|safe }}{% endfor %}
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = '{{ lang }}'

TIME_ZONE = '{{ timezone }}'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/sitestatic/'
STATIC_ROOT = os.path.join(BASE_DIR, 'sitestatic')
STATICFILES_DIRS = (
    '{{ bower_components_dir }}',
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Rest framework settings

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# Modoboa settings
#MODOBOA_CUSTOM_LOGO = os.path.join(MEDIA_URL, "custom_logo.png")

#DOVECOT_LOOKUP_PATH = ('/path/to/dovecot', )

MODOBOA_API_URL = 'https://api.modoboa.org/1/'

# Password validation rules

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
        'syslog-auth': {
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_AUTH,
            'formatter': 'syslog'
        },
        'modoboa': {
            'class': 'modoboa.core.loggers.SQLHandler',
        }
    },
    'loggers': {
        'modoboa.auth': {
            'handlers': ['syslog-auth', 'modoboa'],
            'level': 'INFO',
            'propagate': False
        },
        'modoboa.admin': {
            'handlers': ['modoboa'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Load settings from extensions
{% for extension in extra_settings %}
try:
    from {{ extension }} import settings as {{ extension }}_settings
    {{ extension }}_settings.apply(globals())
except AttributeError:
    from {{ extension }}.settings import *
{% endfor %}
