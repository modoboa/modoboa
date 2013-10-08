##################################
Upgrading an existing installation
##################################

This section contains all the upgrade procedures required to use
newest versions of Modoboa.

.. note::
   Before running a migration, we recommend that you make
   a copy of your existing database.

.. _latestversion:

**************
Latest version
**************

.. warning::

   If you use a version **prior to 0.9.5**, please migrate in two
   steps:
   
   #. first migrate to 0.9.5 
   #. then migrate to the latest version

   If you try to migrate directly, the operation will fail.

Starting with version 0.9.1, Modoboa comes as a standard django
application. Fetch the latest version (see :ref:`get_modoboa`) and
install it.

``pip`` users, just run the following command::

  $ pip install --upgrade modoboa

.. warning::

   If you migrate to **1.1.0**, please follow the :ref:`dedicated migration
   procedure <1.1.0>` and skip the usual one.

Then, refer to this page to check if the version you're installing
requires specific operations. If the version you're looking for is not
present, it means nothing special is required.

Finally, follow the common procedure::

  $ cd <modoboa_instance_dir>
  $ python manage.py syncdb --migrate
  $ python manage.py collectstatic

.. _1.1.0:

1.1.0: FIXME
============

Due to code refactoring, some modifications need to be done into
:file:`settings.py`:

#. ``MODOBOA_APPS`` must contain the following applications::

    MODOBOA_APPS = (
      'modoboa',
      'modoboa.core',
      'modoboa.lib',

      'modoboa.extensions.admin',
      'modoboa.extensions.limits',
      'modoboa.extensions.postfix_autoreply',
      'modoboa.extensions.webmail',
      'modoboa.extensions.stats',
      'modoboa.extensions.amavis',
      'modoboa.extensions.sievefilters',
    )

#. ``AUTH_USER_MODEL`` must be set to ``core.User``

#. Into ``LOGGING``, replace ``modoboa.lib.logutils.SQLHandler`` by
   ``modoboa.core.loggers.SQLHandler``

Then, run the following commands to migrate your installation::

  $ python manage.py migrate core 0001 --fake
  $ python manage.py migrate
  $ python manage.py collectstatic


1.0.1: operations on mailboxes
==============================

The way Modoboa handles **rename** and **delete** operations on
mailboxes has been improved. Make sure to consult :ref:`fs_operations`
and :ref:`Postfix configuration <postfix_config>`. Look at the
``smtpd_recipient_restrictions`` setting.

Run ``modoboa-admin.py postfix_maps --dbtype <mysql|postgres|sqlite>
<tempdir>`` and compare the files with those that postfix currently
use. Make necessary updates in light of the differences

1.0.0: production ready, at last
================================

Configuration file update
-------------------------

Several modifications need to be done into :file:`settings.py`.

#. Add the following import statement::

    from logging.handlers import SysLogHandler

#. Set the ``ALLOWER_HOSTS`` variable::

    ALLOWED_HOSTS = [
        '<your server fqdn>',
    ]

#. Activate the ``django.middleware.csrf.CsrfViewMiddleware``
   middleware and add the ``reversion.middleware.RevisionMiddleware``
   middleware to ``MIDDLEWARE_CLASSES`` like this::

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        # Uncomment the next line for simple clickjacking protection:
        # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'reversion.middleware.RevisionMiddleware',
    
        'modoboa.lib.middleware.AjaxLoginRedirect',
        'modoboa.lib.middleware.CommonExceptionCatcher',
        'modoboa.lib.middleware.ExtControlMiddleware',
    )

#. Add the ``reversion`` application to ``INSTALLED_APPS``

#. Remove all modoboa's application from ``INSTALLED_APPS`` and put
   them into the new ``MODOBOA_APPS`` variable like this::
    
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'south',
        'reversion',
    )

    # A dedicated place to register Modoboa applications
    # Do not delete it.
    # Do not change the order.
    MODOBOA_APPS = (
        'modoboa',
        'modoboa.auth',
        'modoboa.admin',
        'modoboa.lib',
        'modoboa.userprefs',

        'modoboa.extensions.limits',
        'modoboa.extensions.postfix_autoreply',
        'modoboa.extensions.webmail',
        'modoboa.extensions.stats',
        'modoboa.extensions.amavis',
        'modoboa.extensions.sievefilters',
    )
    
    INSTALLED_APPS += MODOBOA_APPS

#. Set the ``AUTH_USER_MODEL`` variable like this::

    AUTH_USER_MODEL = 'admin.User'

#. Modify the logging configuration as follows::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'syslog': {
                'format': '%(name)s: %(levelname)s %(message)s'
            },
        },
        'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'console': {
                # logging handler that outputs log messages to terminal
                'class': 'logging.StreamHandler',
                #'level': 'DEBUG', # message level to be written to console
            },
            'syslog-auth': {
                'class': 'logging.handlers.SysLogHandler',
                'facility': SysLogHandler.LOG_AUTH,
                'formatter': 'syslog'
            },
            'modoboa': {
                'class': 'modoboa.lib.logutils.SQLHandler',
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
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
            }
        }
    }

Postfix and Dovecot configuration update
----------------------------------------

It is necessary to update the queries used to retrieve users and mailboxes:

#. Run ``modoboa-admin.py postfix_maps --dbtype <mysql|postgres> <tempdir>`` and compare the files with those that postfix currently
   use. Make necessary updates in light of the differences

#. Into :file:`dovecot-sql.conf`, update the ``user_query`` query, refer to
   :ref:`dovecot_mysql_queries` or :ref:`dovecot_pg_queries`

#. Update dovecot's configuration to activate the new :ref:`quota related features <dovecot_quota>`

Migration issues
----------------

When running the ``python manage.py syncdb --migrate`` command, you
may encounter the following issues:

#. Remove useless content types

   If the script asks you this question, just reply **no**.

#. South fails to migrate ``reversion``

   Due to the admin user model change, the script :file:`0001_initial.py`
   may fail. Just deactivate ``reversion`` from ``INSTALLED_APPS`` and
   run the command again. Once done, reactivate ``reversion`` and run
   the command one last time.


0.9.4: administrative panel performance improved
================================================

#. Edit the :file:`settings.py` file and remove
   ``'django.contrib.auth.backends.ModelBackend'`` from the
   ``AUTHENTICATION_BACKENDS`` variable

0.9.1: standard django application and more
===========================================

For this version, we recommend to install a new instance (see
:ref:`deployment`) in a different directory.

Then, copy the following content from the old installation to the new
one:

* The :file:`media` directory
* The directory containing RRD files if you use the :ref:`stats` plugin

Don't copy the old :file:`settings.py` file, just keep the new one and
modify it (see :ref:`database` and :ref:`timezone_lang`).

Migrate your database (see :ref:`latestversion`).

Finally, check the :ref:`amavis_frontend`, :ref:`postfix_ar` and
:ref:`stats` chapters (depending on those you use) because the
provided cron scripts have been changed, you must update the way you
call them.

*********************
Modoboa 0.9 and prior
*********************

First, decompress the new tarball at the same location than your
current installation. Then, check if the new version you're installing
requires a migration.

0.9: global UI refactoring, new *limits* extension and more
===========================================================

.. note::
   This version requires at least django 1.3. Make sure to update your
   version before starting to migrate.

.. note::
   Many files have been renamed/removed for this version. I recommend
   that you backup important files (*settings.py*, etc.) elsewhere
   (ie. :file:`/tmp` for example). Then, remove the :file:`modoboa` directory,
   extract the new tarball at the same place, rename the new directory
   to :file:`modoboa` and copy the files you've just backup into it.

.. note::
   If the first super administrator you created is named ``admin``,
   its password will be changed to ``password`` at the end of this
   upgrade. Don't forget to modify it!

#. Edit the :file:`settings.py` file and update the following variables
   (just copy/paste their new content)::

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'modoboa.lib.middleware.AjaxLoginRedirect',
        'modoboa.lib.middleware.CommonExceptionCatcher',
        'modoboa.lib.middleware.ExtControlMiddleware',
    )

    AUTHENTICATION_BACKENDS = (
        'modoboa.lib.authbackends.SimpleBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

#. Add ``django.contrib.staticfiles`` to ``INSTALLED_APPS``

#. Add the following new variables::

    STATIC_ROOT = os.path.join(MODOBOA_DIR, 'sitestatic')
    STATIC_URL = '/sitestatic/'

#. Update the following variables (just copy/paste their new values)::

    MEDIA_ROOT = os.path.join(MODOBOA_DIR, 'media')
    MEDIA_URL = '/media/'

#. **For MySQL users only**, add the following option to your database
   configuration::

    DATABASES = {
        "default" : {
            # ...
            # MySQL users only
            "OPTIONS" : {
                "init_command" : "SET foreign_key_checks = 0;",
            },
        }
    }

#. Add ``'modoboa.extensions.limits'`` to ``INSTALLED_APPS``

#. Update your database (make sure to create a backup before launching
   the following command)::

    $ ./manage.py syncdb --migrate

#. Run the following command to initialize the directory that contains
   static files::

    $ ./manage.py collectstatic

#. If you are using the *stats* extension, please rename the
   :file:`<modoboa_dir>/static/stats` directory to :file:`<modoboa_dir>/media/stats`
   and change the value of the ``IMG_ROOTDIR`` parameter (go to the adminstration panel)

#. Restart the python instance(s) that serve Modoboa

#. Log into Modoboa, go to *Modoboa > Extensions*, uncheck all
   extensions, save. Then, check the extensions you want to use and
   save again

#. Update your webserver configuration to make static files available
   (see :ref:`webservers`)

#. **For Dovecot users only**, you need to modify the
   ``password_query`` (file :file:`/etc/dovecot/dovecot-sql.conf` by default
   on a Debian system) like this::

    password_query = SELECT email AS user, password FROM auth_user WHERE email='%u'

0.8.8: CSV import feature and minor fixes
=========================================

#. Edit the :file:`settings.py` file and add
   ``'modoboa.lib.middleware.AjaxLoginRedirect'`` to the
   ``MIDDLEWARE_CLASSES`` variable like this::

    MIDDLEWARE_CLASSES = (
      'django.middleware.common.CommonMiddleware',
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'django.middleware.locale.LocaleMiddleware',
      'modoboa.lib.middleware.AjaxLoginRedirect',
      'modoboa.lib.middleware.ExtControlMiddleware',
      'modoboa.extensions.webmail.middleware.WebmailErrorMiddleware',
    )

#. Still inside :file:`settings.py`, modify the ``DATABASE_ROUTERS``
   variable like this::

    DATABASE_ROUTERS = ["modoboa.extensions.amavis_quarantine.dbrouter.AmavisRouter"]


0.8.7: per-user language selection
==================================

#. Edit the :file:`settings.py` file and add the
   ``'django.middleware.locale.LocaleMiddleware'`` middleware to the
   ``MIDDLEWARE_CLASSES`` variable like this::

    MIDDLEWARE_CLASSES = (
      'django.middleware.common.CommonMiddleware',
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'django.middleware.locale.LocaleMiddleware',
      'modoboa.lib.middleware.ExtControlMiddleware',
      'modoboa.extensions.webmail.middleware.WebmailErrorMiddleware',
    )

#. To select a custom language, go to *Options > Preferences* and
   select the ``general`` section. Choose a value, save and disconnect
   from Modoboa. On the next login, the desired language will be used.

0.8.6.1: maintenance release
============================

#. If you have tried to create a new mailbox and if you have
   encountered the following `issue
   <http://dev.modoboa.org/ticket/163>`_, you must run the
   ``dbcleanup.py`` script in order to remove orphan records::

    $ cd <modoboa_dir>
    $ PYTHONPATH=$PWD/.. DJANGO_SETTINGS_MODULE=modoboa.settings ./admin/scripts/dbcleanup.py

0.8.6: Quarantine plugin refactoring (using Django's ORM)
=========================================================

#. Just update your configuration if you are using the quarantine
   plugin. Open :file:`settings.py`, move the database configuration from
   the ``DB_CONNECTIONS`` variable to the ``DATABASES`` variable, like
   this::

    DATABASES = {
        "default" : {
            # The default database configuration
        },
        #    ...
        "amavis": {
            "ENGINE" : "<your value>",
            "HOST" : "<your value>",
            "NAME" : "<your value>",
            "USER" : "<your value>",
            "PASSWORD" : "<your value>"
        }
    }

#. Add the new following variable somewhere in the file::

    DATABASE_ROUTERS = ["modoboa.extensions.amavis_quarantine.dbrouter.AmavisRouter"]

#. Remove the deprecated ``DB_CONNECTIONS`` variable from :file:`settings.py`.

0.8.5: new "Sieve filters" plugin, improved admin app
=====================================================

#. Migrate the ``lib`` and ``admin`` applications::

    $ python manage.py migrate lib
    $ python manage.py migrate admin

#. Add ``modoboa.auth`` and ``modoboa.extensions.sievefilters`` to the
   ``INSTALLED_APPS`` variable in :file:`settings.py`.

#. Go the *Settings/Extensions* panel, deactivate and activate your
   extensions, it will update all the symbolic links.

0.8.4: folders manipulation support (webmail) and bugfixes
==========================================================

#. Update the ``MIDDLEWARE_CLASSES`` variable in :file:`settings.py`::

    MIDDLEWARE_CLASSES = (
      'django.middleware.common.CommonMiddleware',
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'modoboa.lib.middleware.ExtControlMiddleware',
      'modoboa.extensions.webmail.middleware.WebmailErrorMiddleware',
    )

#. Go the *Settings/Extensions* panel, deactivate and activate your
   extensions, it will update all the symbolic links to the new format.

#. Optional: update the ``DATABASES`` and ``TEMPLATE_LOADERS``
   variables in :file:`settings.py` to remove warning messages (appearing with
   Django 1.3)::

    DATABASES = {
      "default" : {
        "ENGINE" : "<your engine>",
        "NAME" : "modoboa",
        "USER" : "<your user>",
        "PASSWORD" : "<your password>",
        "HOST" : "",
        "PORT" : ""
      }
    }
  
    TEMPLATE_LOADERS = (
      'django.template.loaders.filesystem.Loader',
      'django.template.loaders.app_directories.Loader',
    )

0.8.3: admin application refactoring and more
=============================================

#. Migrate the ``admin`` application::

     $ python manage.py migrate admin

#. Update SQL queries used in your environnement (see
   :ref:`postfix` or :ref:`dovecot`).

#. Update Postfix configuration so that it can handle domain aliases
   (see :ref:`postfix`).


0.8.2: ckeditor integration and more
====================================

#. Migrate the admin applicaton:: 

     $ python manage.py migrate admin

#. Update your config file and add all extensions to ``INSTALLED_APPS`` 
   (even those you are not going to use).
#. Inside the :file:`<modoboa_dir>/templates/` directory, remove all symbolic links.
#. Download the latest release of ckeditor and extract it into :file:`<modoboa_dir>/static/js/`. It should create a new directory named ``ckeditor``.
#. Update the following variables inside :file:`settings.py`::

     MEDIA_ROOT = os.path.join(MODOBOA_DIR, 'static')
     MEDIA_URL = '/static/'

#. Then, add the following variable: ``MODOBOA_WEBPATH = 'modoboa/'``
#. Delete the following variables: ``STATIC_ROOTDIR`` and
   ``TEMPLATE_CONTEXT_PROCESSORS``.
#. Finally, add ``modoboa.lib.middleware.ExtControlMiddleware`` to
   ``MIDDLEWARE_CLASSES``.

0.8.1 : project renamed
=======================

#. First, rename the ``mailng`` directory to ``modoboa`` and copy all the
   content from ``modoboa-0.8.1`` to ``modoboa``.
#. Edit :file:`settings.py` and replace all occurences of mailng by
   modoboa. Make sure you don't modify the ``DATABASE`` section as you're
   not going to rename your database.
#. Rename the ``MAILNG_DIR`` variable to ``MODOBOA_DIR``.
#. Add ``'django.contrib.messages.middleware.MessageMiddleware'`` to
   ``MIDDLEWARE_CLASSES`` and ``'django.contrib.messages'`` to
   ``INSTALLED_APPS``. Save your modifications.
#. Run the following command::

     $ python manage.py syncdb

#. For all activated extensions, run the following command::
 
     $ export PYTHONPATH=<modoboa_dir>/..=
     $ DJANGO_SETTINGS_MODULE=modoboa.settings <modoboa_dir>/scripts/extension.py <extension> on

#. Update your webserver configuration and restart it.

0.8 : SQL migration needed
==========================

Before you start the migration, make sure you have updated your
``INSTALLED_APPS`` variable and that it contains at least::

  INSTALLED_APPS = (
     # Django's stuff before

     'south',
     'mailng',
     'mailng.lib',
     'mailng.admin',
     'mailng.userprefs',
  )

Starting with 0.8, ``mailng.main`` doesn't exist anymore. You must remove
it from your ``INSTALLED_APPS``.

Finally, run the following commands::

  $ python manage.py syncdb
  $ python manage.py convert_to_south
  $ python manage.py migrate --all 0001 --fake
  $ python manage.py migrate --all 0002

