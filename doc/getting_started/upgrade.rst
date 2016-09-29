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
