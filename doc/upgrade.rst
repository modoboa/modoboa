#######
Upgrade
#######

Modoboa
*******

.. warning::

   The new version you are going to install may need to modify your
   database. Before you start, make sure to backup everything!

Most of the time, upgrading your installation to a newer Modoboa
version only requires a few actions. In every case, you will need to
apply the general procedure first and then check if the version you
are installing requires specific actions.

In case you use a dedicated user and/or a virtualenv, do not forget to
use them:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate

Then, run the following commands:

.. sourcecode:: bash

   > pip install modoboa==<VERSION>
   > cd <modoboa_instance_dir>
   > python manage.py migrate
   > python manage.py collectstatic
   > python manage.py check --deploy

Once done, check if the version you are installing requires
:ref:`specific_upgrade_instructions`.

Finally, restart your web server.

Sometimes, you might need to upgrade postfix map files too. To do so,
just run the ``generate_postfix_maps`` command on the same directory
than the one used for installation (:file:`/etc/postfix` by default).

Make sure to use root privileges and run the following command:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <directory>

Then, reload postfix.

Extensions
**********

If a new version is available for an extension you're using, it is
recommanded to install it. Upgrading an extensions is pretty and the
procedure is almost the same than the one used for Modoboa.

In case you use a dedicated user and/or a virtualenv, do not forget to
use them:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate

Then, run the following commands:

.. sourcecode:: bash

   > pip install <EXTENSION>==<VERSION>
   > cd <modoboa_instance_dir>
   > python manage.py migrate
   > python manage.py collectstatic
   > python manage.py check --deploy

Finally, restart your web server.

It is a generic upgrade procedure which will be enough most of the
time but it is generally a good idea to check the associated
documentation.

Rebuild Virtual Environment
***************************

.. include:: rebuild_virtual_env.rst

.. _specific_upgrade_instructions:

Specific instructions
*********************

1.14.0
======

This release introduces an optional LDAP synchronization process. If
you want to use it, please follow the :ref:`dedicated procedure <ldap_sync>`.

1.13.1
======

Upgrade postfix maps files as follows:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <path> --force-overwrite


1.13.0
======

Add ``'modoboa.dnstools'`` to ``MODOBOA_APPS``:

.. sourcecode:: python

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
   )

Add the following new settings:

.. sourcecode:: python

   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True

modoboa-postfix-autoreply 1.5.0
===============================

Edit the :file:`/etc/postfix/main.cf` file and remove the
``sql-autoreplies-transport.cf`` map from the ``transport_maps`` if
present. Remove the corresponding ``proxy_read_maps`` entry if relevant.

Reload postfix.

1.10.0
======

.. warning::

   Upgrade installed extensions BEFORE running ``check`` or
   ``migrate`` commands.

Upgrade all your installed plugins to the following versions:

.. warning::

   If you use the amavis plugin, make sure to include its
   configuration as follows into :file:`settings.py`:

   .. sourcecode:: python

      from modoboa_amavis import settings as modoboa_amavis_settings
      modoboa_amavis_settings.apply(globals())

+------------------------------+------------------------------+
|Name                          |Version                       |
+==============================+==============================+
|modoboa-amavis                |1.2.0                         |
+------------------------------+------------------------------+
|modoboa-contacts              |0.5.0                         |
+------------------------------+------------------------------+
|modoboa-dmarc                 |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-imap-migration        |1.2.0                         |
+------------------------------+------------------------------+
|modoboa-pdfcredentials        |1.3.0                         |
+------------------------------+------------------------------+
|modoboa-postfix-autoreply     |1.4.0                         |
+------------------------------+------------------------------+
|modoboa-radicale              |1.2.0                         |
+------------------------------+------------------------------+
|modoboa-sievefilters          |1.4.0                         |
+------------------------------+------------------------------+
|modoboa-stats                 |1.4.0                         |
+------------------------------+------------------------------+
|modoboa-webmail               |1.4.0                         |
+------------------------------+------------------------------+

Edit the :file:`settings.py` file and apply the following modifications.

Add ``'modoboa.transport'`` to ``MODOBOA_APPS``:

.. sourcecode:: python

   MODOBOA_APPS = (
      'modoboa',
      'modoboa.core',
      'modoboa.lib',
      'modoboa.admin',
      'modoboa.transport',
      'modoboa.relaydomains',
      'modoboa.limits',
      'modoboa.parameters',
   )

Replace the following line:

.. sourcecode:: python

   MIDDLEWARE_CLASSES = (

by:

.. sourcecode:: python

   MIDDLEWARE = (

Update postfix map files as follows:

.. sourcecode:: bash

   > rm -f <path>/modoboa-postfix-maps.chk
   > python manage.py generate_postfix_maps --force --destdir <path>

Then, modify postfix's configuration as follows::

    smtpd_sender_login_maps =
      <driver>:<path>/sql-sender-login-map.cf

    transport_maps =
      <driver>:<path>/sql-transport.cf
      <driver>:<path>/sql-spliteddomains-transport.cf
      # other map files...

Replace ``<driver>`` and ``<path>`` by your values.

If ``transport_maps`` contains ``sql-relaydomains-transport.cf``, remove it.

.. warning::

   If you make use of postfix's `proxymap server
   <http://www.postfix.org/proxymap.8.html>`_, you must also update
   the ``proxy_read_maps`` setting.

Reload postfix.

Add the following cron job in order to generate DKIM keys::

  # Generate DKIM keys (they will belong to the user running this job)
  *       *       *       *       *       root    $PYTHON $INSTANCE/manage.py modo manage_dkim_keys

1.9.0
=====

If you want to manage inactive accounts, look at :ref:`inactive_accounts`.

1.8.3
=====

Edit the :file:`settings.py` file and replace the following line:

.. sourcecode:: python

   BASE_DIR = os.path.dirname(os.path.dirname(__file__))

by:

.. sourcecode:: python

   BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

1.8.0
=====

Modoboa now relies on `Django's builtin password validation system
<https://docs.djangoproject.com/en/1.10/topics/auth/passwords/#module-django.contrib.auth.password_validation>`_
to validate user passwords, instead of ``django-passwords``.

Remove ``django-passwords`` from your system:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate
   > pip uninstall django-passwords

Edit the :file:`settings.py` file and remove the following content:

.. sourcecode:: python

   # django-passwords

   PASSWORD_MIN_LENGTH = 8

   PASSWORD_COMPLEXITY = {
       "UPPER": 1,
       "LOWER": 1,
       "DIGITS": 1
   }

Add the following lines:

.. sourcecode:: python

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

1.7.2
=====

API documentation has evolved (because of the upgrade to Django Rest
Framework 3.6) and CKeditor is now embedded by default (thanks to the
``django-ckeditor`` package). Some configuration changes are
required.

Edit your :file:`settings.py` file and apply the following modifications:

* Update the ``INSTALLED_APPS`` variable as follows:

.. sourcecode:: python

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
   )

* Update the ``REST_FRAMEWORK`` variable as follows:

.. sourcecode:: python

   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'rest_framework.authentication.TokenAuthentication',
           'rest_framework.authentication.SessionAuthentication',
       ),
   }

* Remove the ``SWAGGER_SETTINGS`` variable

* Add the following content

.. sourcecode:: python

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

Don't forget to run the following command:

.. sourcecode:: bash

   > python manage.py collectstatic


1.7.1
=====

If you used 1.7.0 for a fresh installation, please run the following commands:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate
   > cd <modoboa_instance_dir>
   > python manage.py load_initial_data

1.7.0
=====

This version requires Django >= 1.10 so you need to make some
modifications. It also brings internal API changes which are not
backward compatible so installed extensions must be upgraded too.

First of all, deactivate all installed extensions (edit the
:file:`settings.py` file and comment the corresponding lines in
``MODOBOA_APPS``).

Edit the :file:`urls.py` file of your local instance and replace its
content by the following one:

.. sourcecode:: python

   from django.conf.urls import include, url

   urlpatterns = [
       url(r'', include('modoboa.urls')),
   ]

Edit the :file:`settings.py` and apply the following changes:

* Add ``'modoboa.parameters'`` to ``MODOBOA_APPS``:

.. sourcecode:: python

   MODOBOA_APPS = (
       'modoboa',
       'modoboa.core',
       'modoboa.lib',
       'modoboa.admin',
       'modoboa.relaydomains',
       'modoboa.limits',
       'modoboa.parameters',
       # Modoboa extensions here.
   )

* Add ``'modoboa.core.middleware.LocalConfigMiddleware'`` to ``MIDDLEWARE_CLASSES``:

.. sourcecode:: python

   MIDDLEWARE_CLASSES = (
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

* Modoboa used to provide a custom authentication backend
  (``modoboa.lib.authbackends.SimpleBackend``) but it has been
  removed. Replace it as follows:

.. sourcecode:: python

   AUTHENTICATION_BACKENDS = (
       # Other backends before...
       'django.contrib.auth.backends.ModelBackend',
   )

* Remove ``TEMPLATE_CONTEXT_PROCESSORS`` and replace it by:

.. sourcecode:: python

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
               'debug': False,
           },
       },
   ]

Run the following commands (load virtualenv if you use one):

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate
   > cd <modoboa_instance_dir>
   > python manage.py migrate
   > python manage.py collectstatic

Finally, upgrade your extensions and reactivate them.

+------------------------------+------------------------------+
|Name                          |Version                       |
+==============================+==============================+
|modoboa-amavis                |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-dmarc                 |1.0.0                         |
+------------------------------+------------------------------+
|modoboa-imap-migration        |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-pdfcredentials        |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-postfix-autoreply     |1.2.0                         |
+------------------------------+------------------------------+
|modoboa-radicale              |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-sievefilters          |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-stats                 |1.1.0                         |
+------------------------------+------------------------------+
|modoboa-webmail               |1.1.0                         |
+------------------------------+------------------------------+

Command line shortcuts:

.. sourcecode:: bash

   $ pip install modoboa-amavis==1.1.0
   $ pip install modoboa-dmarc==1.0.0
   $ pip install modoboa-imap-migration==1.1.0
   $ pip install modoboa-pdfcredentials==1.1.0
   $ pip install modoboa-postfix-autoreply==1.2.0
   $ pip install modoboa-radicale==1.1.0
   $ pip install modoboa-sievefilters==1.1.0
   $ pip install modoboa-stats==1.1.0
   $ pip install modoboa-webmail==1.1.0

And please make sure you use the latest version of the
``django-versionfield2`` package:

.. sourcecode:: bash

   $ pip install -U django-versionfield2

Notes about quota changes and resellers
---------------------------------------

Reseller users now have a quota option in Resources tab. This is the quota
that a reseller can share between all its domains.

There are two quotas for a domain in the new version:

1. Quota &
2. Default mailbox quota.

[1]. Quota: quota shared between mailboxes
This quota is shared between all the mailboxes of this domain. This
value cannot exceed reseller's quota and hence cannot be 0(unlimited)
if reseller has finite quota.

[2]. Default mailbox quota: default quota applied to mailboxes
This quota is the default quota applied to new mailboxes. This value
cannot exceed Quota[1] and hence cannot be 0(unlimited) if Quota[1] is
finite.

1.6.1
=====

First of all, update postfix map files as follows:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <path> --force-overwrite

Then, modify postfix's configuration as follows::

  smtpd_sender_login_maps =
      <driver>:<path>/sql-sender-login-mailboxes.cf
      <driver>:<path>/sql-sender-login-aliases.cf
      <driver>:<path>/sql-sender-login-mailboxes-extra.cf

Replace ``<driver>`` and ``<path>`` by your values.

Finally, reload postfix.

This release also deprecates some internal functions. As a result,
several extensions has been updated to maintain the compatibility. If
you enabled the notification service, you'll find the list of
available updates directly in your Modoboa console.

For the others, here is the list:

+------------------------------+------------------------------+
|Name                          |Version                       |
+==============================+==============================+
|modoboa-amavis                |1.0.10                        |
+------------------------------+------------------------------+
|modoboa-postfix-autoreply     |1.1.7                         |
+------------------------------+------------------------------+
|modoboa-radicale              |1.0.5                         |
+------------------------------+------------------------------+
|modoboa-stats                 |1.0.9                         |
+------------------------------+------------------------------+

Command line shortcut:

.. sourcecode:: bash

  $ pip install modoboa-amavis==1.0.10
  $ pip install modoboa-postfix-autoreply==1.1.7
  $ pip install modoboa-radicale==1.0.5
  $ pip install modoboa-stats==1.0.9


1.6.0
=====

.. warning::

   You have to upgrade extensions due to `core.User` model attribute change (`user.group` to `user.role`).
   Otherwise, you will have an internal error after upgrade.
   In particular: `modoboa-amavisd <https://github.com/modoboa/modoboa-amavis/commit/35df4e48b124e56df930cda8c013af0c1fcaabf3>`_, `modoboa-stats <https://github.com/modoboa/modoboa-stats/commit/aa4a39ce65eb306ad6dec30a54eb58945b120274>`_, `modoboa-postfix-autoreply <https://github.com/modoboa/modoboa-postfix-autoreply/commit/20f98c8d1c0c0dbd420f47aefcbb0290022414a4>`_ are concerned.

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
