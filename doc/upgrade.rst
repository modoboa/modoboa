#######
Upgrade
#######

.. warning::

   The new version you are going to install may need to modify your
   database. Before you start, make sure to backup everything!

Most of the time, upgrading your installation to a newer Modoboa
version only requires a few actions. In any case, you will need to
apply the general procedure first and then check if the version you
are installing requires specific actions.

.. note::
   
   In case you use a dedicated user and/or a virtualenv, do not forget to
   use them:

   .. sourcecode:: bash

     > sudo -i <modoboa_user>
     > source <virtuenv_path>/bin/activate

The general procedure is as follows::

  > pip install modoboa==<VERSION>
  > cd <modoboa_instance_dir>
  > python manage.py migrate
  > python manage.py collectstatic

Once done, check if the version you are installing requires
:ref:`specific_upgrade_instructions`.
  
Finally, restart your web server.

.. _specific_upgrade_instructions:

Specific instructions
*********************

1.6.0
=====

An interesting feature brougth by this version is the capability to
make different checks about MX records. For example, Modoboa can
query main `DNSBL <https://en.wikipedia.org/wiki/DNSBL>`_ providers
for every defined domain. With this, you will quickly now if one the
domains you manage is listed or not. To activate it, add the
following line to your crontab::

  */30 * * * * <modoboa_site>/manage.py modo check_mx

The communication with Modoboa public API has been reworked. Instead
of sending direct synchronous queries (for example to check new
versions), a cron job has been added. To activate it, add the
following line to your crontab::

  0 * * * * <modoboa_site>/manage.py communicate_with_public_api

Please also note that public API now uses TLS so you must update your
configuration as follows::

  MODOBOA_API_URL = 'https://api.modoboa.org/1/'

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
