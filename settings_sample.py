# Django settings for modoboa project.
import os.path

DEBUG = False 
TEMPLATE_DEBUG = DEBUG

MODOBOA_DIR = os.path.dirname(__file__)
MODOBOA_WEBPATH = "modoboa/"

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default" : {
        "ENGINE" : "",
        "NAME" : "modoboa",
        "USER" : "",
        "PASSWORD" : "",
        "HOST" : "",
        "PORT" : ""
    },
    # "pfxadmin" : {
    #     "ENGINE" : "",
    #     "NAME" : "",
    #     "USER" : "",
    #     "PASSWORD"
    # }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

LOGIN_REDIRECT_URL = '/modoboa/admin/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(MODOBOA_DIR, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '2)e+la#y$1b&v!p)s^&4lwpc92o59fye)mj^3^7$jytmvx379d'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'modoboa.lib.middleware.ExtControlMiddleware',
    'modoboa.extensions.webmail.middleware.WebmailErrorMiddleware',
)

ROOT_URLCONF = 'modoboa.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'south',
    'modoboa',
    'modoboa.auth',
    'modoboa.lib',
    'modoboa.admin',
    'modoboa.userprefs',

    # Modoboa extensions here.
    'modoboa.extensions.postfix_autoreply',
    'modoboa.extensions.webmail',
    'modoboa.extensions.stats',
    'modoboa.extensions.amavis_quarantine',
    'modoboa.extensions.sievefilters',

    # Extra tools
    # 'modoboa.tools.pfxadmin_migrate',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'modoboa.lib.authbackends.SimpleBackend'
)

# Amavis quarantine
# DB_CONNECTIONS = (
#     {"amavis_quarantine" : {"driver"   : "",
#                             "host"     : "",
#                             "dbname"   : "",
#                             "login"    : "",
#                             "password" : ""}
#      }
#     )


#SESSION_COOKIE_AGE = 300
#CACHE_BACKEND = 'file://'
