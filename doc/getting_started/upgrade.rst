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

Fetch the latest version (see :ref:`get_modoboa`) and install
it. ``pip`` users, just run the following command::

  $ pip install modoboa==<VERSION>

Replace ``<VERSION>`` by the appropriate value.

As for a fresh installation, ``modoboa-admin.py`` can be used to
upgrade your local configuration. To do so, remove the directory where
your instance was first deployed::

  $ rm -rf <modoboa_instance_dir>

.. warning::
     
   If you customized your configuration file (:file:`settings.py`) with
   non-standard settings, you'll have to re-apply them.

Finally, run the ``deploy`` comamand. Make sure to consult the
:ref:`deployment` section to know more about the available options.

If you prefer the manual way, check if
:ref:`specific_upgrade_instructions` are required according to the
version you're installing.

To finish, restart the web server process according to the environment
you did choose. See :ref:`webservers` for more details.

.. _specific_upgrade_instructions:

*****************************
Specific upgrade instructions
*****************************

1.6.0
=====

An interesting feature brougth by this version is the capability to
make different checks about MX records. For example, Modoboa can
query main `DNSBL <https://en.wikipedia.org/wiki/DNSBL>`_ providers
for every defined domain. With this, you will quickly know if one the
domains you manage is listed or not. To activate it, add the
following line to your crontab::

  */30 * * * * <optional_virtualenv_path/>python <modoboa_instance_dir>/manage.py modo check_mx

The communication with Modoboa public API has been reworked. Instead
of sending direct synchronous queries (for example to check new
versions), a cron job has been added. To activate it, add the
following line to your crontab::

  0 * * * * <optional_virtualenv_path/>python <modoboa_instance_dir>/manage.py communicate_with_public_api

Please also note that public API now uses TLS so you must update your
configuration as follows::

  MODOBOA_API_URL = 'https://api.modoboa.org/1/'

Finally, it is now possible to declare additional sender addresses on
a per-account basis. You need to update your postfix configuration in
order to use this functionality. Just edit the :file:`main.cf` file
and change the following parameter::

  smtpd_sender_login_maps =
      <driver>:/etc/postfix/sql-sender-login-mailboxes.cf
      <driver>:/etc/postfix/sql-sender-login-aliases.cf
      <driver>:/etc/postfix/sql-sender-login-mailboxes-extra.cf

1.5.0
=====

The API has been greatly improved and a documentation is now
available. To enable it, add ``'rest_framework_swagger'`` to the
``INSTALLED_APPS`` variable in :file:`settings.py` as follows::

  INSTALLED_APPS = (
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.sites',
      'django.contrib.staticfiles',
      'reversion',
      'rest_framework.authtoken',
      'rest_framework_swagger',
  )

Then, add the following content into :file:`settings.py`, just after
the ``REST_FRAMEWORK`` variable::

  SWAGGER_SETTINGS = {
      "is_authenticated": False,
      "api_version": "1.0",
      "exclude_namespaces": [],
      "info": {
          "contact": "contact@modoboa.com",
          "description": ("Modoboa API, requires a valid token."),
          "title": "Modoboa API",
      }
  }

You're done. The documentation is now available at the following address:

  http://<your instance address>/docs/api/

Finally, if you find a ``TEMPLATE_CONTEXT_PROCESSORS`` variable in
your :file:`settings.py` file, make sure it looks like this::

  TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + [
      'modoboa.core.context_processors.top_notifications',
  ]

1.4.0
=====

.. warning::

   Please make sure to use Modoboa 1.3.5 with an up-to-date database
   before an upgrade to 1.4.0.

.. warning::

   Do not follow the regular upgrade procedure for this version.   

Some extension have been moved back into the main repository. The main
reason for that is that using Modoboa without them doesn't make sense.

First of all, you must rename the following applications listed inside
the ``MODOBOA_APPS`` variable:

+--------------------------+--------------------+
|Old name                  |New name            |
+==========================+====================+
|modoboa_admin             |modoboa.admin       |
+--------------------------+--------------------+
|modoboa_admin_limits      |modoboa.limits      |
+--------------------------+--------------------+
|modoboa_admin_relaydomains|modoboa.relaydomains|
+--------------------------+--------------------+

Then, apply the following steps:

#. Uninstall old extensions::

   $ pip uninstall modoboa-admin modoboa-admin-limits modoboa-admin-relaydomains

#. Install all extension updates using pip (check the *Modoboa > Information* page)
   
#. Manually migrate database::

   $ cd <instance_dir>
   $ python manage.py migrate auth
   $ python manage.py migrate admin 0001 --fake
   $ python manage.py migrate admin
   $ python manage.py migrate limits 0001 --fake
   $ python manage.py migrate relaydomains 0001 --fake
   $ python manage.py migrate

#. Finally, update static files::

   $ python manage.py collectstatic

This version also introduces a REST API. To enable it:

#. Add ``'rest_framework.authtoken'`` to the ``INSTALLED_APPS`` variable

#. Add the following configuration inside ``settings.py``::
        
     # Rest framework settings

     REST_FRAMEWORK = {
         'DEFAULT_AUTHENTICATION_CLASSES': (
             'rest_framework.authentication.TokenAuthentication',
         ),
         'DEFAULT_PERMISSION_CLASSES': (
             'rest_framework.permissions.IsAuthenticated',
         )
     }

#. Run the following command::

   $ python manage.py migrate

1.3.5
=====

To enhance security, Modoboa now checks the `strength of user
passwords <https://github.com/dstufft/django-passwords>_`.

To use this feature, add the following configuration into the ``settings.py`` file::

  # django-passwords

  PASSWORD_MIN_LENGTH = 8

  PASSWORD_COMPLEXITY = {
      "UPPER": 1,
      "LOWER": 1,
      "DIGITS": 1
  }


1.3.2
=====

Modoboa now uses the *atomic requests* mode to preserve database
consistency (`reference
<https://docs.djangoproject.com/en/1.7/topics/db/transactions/#tying-transactions-to-http-requests>`_).

To enable it, update the ``DATABASES`` variable in ``settings.py`` as
follows::

  DATABASES = {
      "default": {
          # stuff before...
          "ATOMIC_REQUESTS": True
      },
      "amavis": {
          # stuff before...
          "ATOMIC_REQUESTS": True
      }
  }

1.3.0
=====

This release does not bring awesome new features but it is a necessary
bridge to the future of Modoboa. All extensions now have their own git
repository and the deploy process has been updated to reflect this
change.

Another important update is the use of Django 1.7. Besides its new
features, the migration system has been reworked and is now more
robust than before.

Before we begin with the procedure, here is a table showing old
extension names and their new name:

+----------------------------------------+--------------------------+--------------------------+
|Old name                                |New package name          |New module name           |
+========================================+==========================+==========================+
|modoboa.extensions.admin                |modoboa-admin             |modoboa_admin             |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.limits               |modoboa-admin-limits      |modoboa_admin_limits      |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.postfix_autoreply    |modoboa-postfix-autoreply |modoboa_postfix_autoreply |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.postfix_relay_domains|modoboa-admin-relaydomains|modoboa_admin_relaydomains|
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.radicale             |modoboa-radicale          |modoboa_radicale          |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.sievefilters         |modoboa-sievefilters      |modoboa_sievefilters      |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.stats                |modoboa-stats             |modoboa_stats             |
+----------------------------------------+--------------------------+--------------------------+
|modoboa.extensions.webmail              |modoboa-webmail           |modoboa_webmail           |
+----------------------------------------+--------------------------+--------------------------+

Here are the required steps:

#. Install the extensions using pip (look at the second column in the table above)::

   $ pip install <the extensions you want>

#. Remove ``south`` from ``INSTALLED_APPS``

#. Rename old extension names inside ``MODOBOA_APPS`` (look at the third column in the table above)

#. Remove ``modoboa.lib.middleware.ExtControlMiddleware`` from ``MIDDLEWARE_CLASSES``

#. Change ``DATABASE_ROUTERS`` to::

    DATABASE_ROUTERS = ["modoboa_amavis.dbrouter.AmavisRouter"]

#. Run the following commands::

   $ cd <modoboa_instance_dir>
   $ python manage.py migrate

#. Reply ``yes`` to the question

#. Run the following commands::

   $ python manage.py load_initial_data
   $ python manage.py collectstatic

#. The cleanup job has been renamed in Django, so you have to modify your crontab entry::

   - 0 0 * * * <modoboa_site>/manage.py cleanup
   + 0 0 * * * <modoboa_site>/manage.py clearsessions

1.2.0
=====

A new notification service let administrators know about new Modoboa
versions. To activate it, you need to update the
``TEMPLATE_CONTEXT_PROCESSORS`` variable like this::

  from django.conf import global_settings
  
  TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'modoboa.core.context_processors.top_notifications',
  )

and to define the new ``MODOBOA_API_URL`` variable::

  MODOBOA_API_URL = 'http://api.modoboa.org/1/'

The location of external static files has changed. To use them, add a
new path to the ``STATICFILES_DIRS``::

  # Additional locations of static files
  STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "<path/to/modoboa/install/dir>/bower_components",
  )

Run the following commands to define the hostname of your instance::

  $ cd <modoboa_instance_dir>
  $ python manage.py set_default_site <hostname>

If you plan to use the Radicale extension:

#. Add ``'modoboa.extensions.radicale'`` to the ``MODOBOA_APPS`` variable

#. Run the following commands::

     $ cd <modoboa_instance_dir>
     $ python manage.py syncdb

.. warning::

    You also have to note that the :file:`sitestatic` directory has moved from
    ``<path to your site's dir>`` to ``<modoboa's root url>`` (it's probably
    the parent directory). You have to adapt your web server configuration
    to reflect this change.
     
1.1.7: manual learning for SpamAssassin
=======================================

A new feature allows administrators and users to manually train
SpamAssassin in order to customize its behaviour.

Check :ref:`amavis:sa_manual_learning` to know more about this feature.

1.1.6: Few bugfixes
===================

Catchall aliases were not really functional until this version as they
were eating all domain traffic.

To fix them, a postfix map file (``sql-mailboxes-self-aliases.cf``)
has been re-introduced and must be listed into the
``virtual_alias_maps`` setting. See :ref:`postfix_config` for the
order.

1.1.2: Audit trail issues
=========================

Update the :file:`settings.py` file as follows:

#. Remove the ``'reversion.middleware.RevisionMiddleware'``
   middleware from the ``MIDDLEWARE_CLASSES`` variable

#. Add the new ``'modoboa.lib.middleware.RequestCatcherMiddleware'``
   middleware at the end of the ``MIDDLEWARE_CLASSES`` variable

1.1.1: Few bugfixes
===================

For those who installed Dovecot in a non-standard location, it is now
possible to tell Modoboa where to find it. Just define a variable
named ``DOVECOT_LOOKUP_PATH`` in the :file:`settings.py` file and
include the appropriate lookup path inside::

  DOVECOT_LOOKUP_PATH = ("/usr/sbin/dovecot", "/usr/local/sbin/dovecot")

.. _1.1.0:

1.1.0: relay domains and better passwords encryption
====================================================

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

#. Add ``'modoboa.extensions.postfix_relay_domains'`` to
   ``MODOBOA_APPS``, just before
   ``'modoboa.extensions.limits'``

#. ``AUTH_USER_MODEL`` must be set to ``core.User``

#. Into ``LOGGING``, replace ``modoboa.lib.logutils.SQLHandler`` by
   ``modoboa.core.loggers.SQLHandler``

Then, run the following commands to migrate your installation::

  $ python manage.py syncdb
  $ python manage.py migrate core 0001 --fake
  $ python manage.py migrate
  $ python manage.py collectstatic

Finally, update both :ref:`Dovecot <dovecot_authentication>` and
:ref:`Postfix <postfix>` queries.

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
