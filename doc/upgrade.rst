#######
Upgrade
#######

Modoboa
*******

.. note::
   In this doc, ``by default`` means that you used `modoboa installer
   <https://github.com/modoboa/modoboa-installer>`_ to install modoboa
   and that your didn't change your configuration.

.. warning::

   The new version you are going to install may need to modify your
   database. Before you start, make sure to backup everything!

Most of the time, upgrading your installation to a newer Modoboa
version only requires a few actions. In every case, you will need to
apply the specific actions if the version you are installing requires it,
and then apply the general ones.

In case you use a dedicated user and/or a virtualenv, do not forget to
use them:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
   > source <virtuenv_path>/bin/activate


.. _post_upgrade_commands:

.. note::

    Check the :ref:`specific_upgrade_instructions` before running the following commands.

Then, run the following commands:

.. sourcecode:: bash

   > pip install modoboa==<VERSION>
   > cd <modoboa_instance_dir>
   > python manage.py migrate
   > python manage.py collectstatic
   > python manage.py check --deploy
   > python manage.py load_initial_data

Then when everything has been updated,
restart modoboa's services:

.. sourcecode:: bash

   # sudo systemctl restart uwsgi
   # sudo systemctl restart supervisor

Finally, restart your web server.

Sometimes, you might need to upgrade postfix map files too. To do so,
just run the ``generate_postfix_maps`` command on the same directory
than the one used for installation (:file:`/etc/postfix` by default).

Make sure to use root privileges and run the following command:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <directory>

Then, reload postfix.


Modoboa installer
*****************

It is important to keep the installer updated because it works on rolling release.
To do that, go to modoboa-installer directory then:

.. sourcecode:: bash

   > git fetch && git pull

If some error appears, you may try this:

.. sourcecode:: bash

   > git reset --hard origin/master


New-admin interface
*******************

.. note::
   You don't need to perform these actions if you use the installer to upgrade your instance.

New admin interface won't update by itself. Run the following commands to update it:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
   > cd <modoboa_instance_dir>
   > cp frontend/config.json ./
   > rm -rf frontend
   > cp -R <virtuenv_path>/lib/pythonX.X/site-packages/modoboa/frontend_dist/ frontend/
   > cp ./config.json frontend/config.json

Extensions
**********

..  warning::
   Do not open an issue after an upgrade if you have not updated your extensions.

If a new version is available for an extension you're using, it is
recommanded to install it. It may even be required.
Upgrading an extensions is pretty and the
procedure is almost the same than the one used for Modoboa.

In case you use a dedicated user and/or a virtualenv, do not forget to
use them:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
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

Version 2.3.3
=============

.. warning::

   The ``crypt ({CRYPT})`` password scheme has been marked as
   deprecated and will be removed from Modoboa starting with version
   **2.4.0**. If you are still using this weak scheme, you must change
   to something safer **ASAP**. Installations still using this scheme
   won't be able to install Modoboa 2.4 and upper...

Update your :file:`settings.py` file with following content:

.. sourcecode:: python

   SILENCED_SYSTEM_CHECKS = [
       "security.W019",  # modoboa uses iframes to display e-mails
       "ckeditor.W001",  # CKEditor 4.22.1 warning
   ]

This will silence a `warning sent by django-ckeditor <https://github.com/modoboa/modoboa/issues/3316>`_.

Version 2.3.0
=============

.. warning::

   For this particular version, it is really important that you apply
   new migrations **AFTER** the following instructions. If you don't,
   you'll get into trouble...

Pre update
----------

.. note::

    To check that you were actually using modoboa-postfix-autoreply
    you can check if this command returns something:

    .. sourcecode:: bash

        cat /srv/modoboa/instance/instance/settings.py | grep "modoboa_postfix_autoreply"

If you were using
`modoboa-postfix-autoreply <https://github.com/modoboa/modoboa-postfix-autoreply>`_
extension, you need to perfome a few commands:

-  If you are using Postegresql (default option with the installer),
   run as a root user:

   .. sourcecode:: bash

       > sudo -u postgres -i psql -d "modoboa" -c "UPDATE django_content_type SET app_label='postfix_autoreply' WHERE app_label='modoboa_postfix_autoreply'"
       > sudo -u postgres -i psql -d "modoboa" -c "UPDATE django_migrations SET app='postfix_autoreply' WHERE app='modoboa_postfix_autoreply'"

-   If you are using Mysql, run as a root user:

    .. sourcecode:: bash

       > echo "UPDATE django_content_type SET app_label='postfix_autoreply' WHERE app_label='modoboa_postfix_autoreply'" |  mysql -u root -p modoboa
       > echo "UPDATE django_migrations SET app='postfix_autoreply' WHERE app='modoboa_postfix_autoreply'" | mysql -u root -p modoboa

Required changes to :file:`settings.py`
---------------------------------------

Some changes are required to your :file:`settings.py` file.
These changes will not be performed by the installer.
The location of this file is ``/srv/modoboa/instance/instance``
by default.

-  Append ``'import environ'`` after ``'import os'``:

   .. sourcecode:: python

      import os
      import environ

-  Append the following lines after the line starting
   with ``'BASE_DIR'``:

   .. sourcecode:: python

      # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
      BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
      env = environ.Env()
      environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

-  Add ``oauth2_provider`` and ``corsheaders`` to the ``INSTALLED_APPS`` list:

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
      )

-  The ``modoboa-postfix-autoreply`` and ``modoboa-sievefilters``
   plugins have been merged into the core.

   Add ``'modoboa.postfix_autoreply'`` and
   ``modoboa.sievefilters`` to ``MODOBOA_APPS``:

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
         'modoboa.policyd',
         'modoboa.maillog',
         'modoboa.dmarc',
         'modoboa.pdfcredentials',
         'modoboa.imap_migration',
         'modoboa.postfix_autoreply',
         'modoboa.sievefilters',
      )

   .. warning::
      Remove any reference to ``'modoboa_postfix_autoreply'`` AND
      ``modoboa_sievefilters`` in this same variable.

-  Due to the changes to the authentication flow, you need to replace MIDDLEWARE
   with the following:

   .. sourcecode:: python

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

-  Replace
   ``'modoboa.core.drf_authentication.JWTAuthenticationWith2FA'`` by
   ``'oauth2_provider.contrib.rest_framework.OAuth2Authentication'``
   at the top of the list of ``DEFAULT_AUTHENTICATION_CLASSES``
   (inside ``REST_FRAMEWORK`` section):

   .. sourcecode:: python

      'DEFAULT_AUTHENTICATION_CLASSES': (
         'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
         'rest_framework.authentication.TokenAuthentication',
         'rest_framework.authentication.SessionAuthentication',
      ),

Save your modifications at this point and run the :ref:`post upgrade
commands <post_upgrade_commands>` now.

Then, apply this last modification to your settings:

-  Run the commands indicated :ref:`in the first section <post_upgrade_commands>`
   then add the following content after ``MEDIA_ROOT``:

   .. sourcecode:: python

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

Docevot configuration changes
-----------------------------

You must enable oauth2 authentication in Dovecot to make the filters
editor work in the new UI. Follow this :ref:`guide <dovecot_oauth2>`.

Post update
-----------

Run this command to be sure to have everything set.

.. sourcecode:: bash

    python manage.py modo repair

You need to set the ``buffer-size`` to ``8192`` in uwsgi config.
Edit the value in ``/etc/uwsgi/apps-available/automx_instance.ini``
to match at least 8192 or add it if it was not set:

.. sourcecode:: bash

    buffer-size = 8192


SORBS DNS
---------

   .. note::
      The installer will take care of that if you use it to upgrade.


   `SORBS DNS has been deprecated <https://www.mail-archive.com/mailop@mailop.org/msg22064.html>`_.
   If you were using them with postfix, you need to update your
   configuration by removing any reference to it. For example::

      # Use some DNSBL
      postscreen_dnsbl_sites =
         zen.spamhaus.org=127.0.0.[2..11]*3
         bl.spameatingmonkey.net=127.0.0.2*2
         bl.spamcop.net=127.0.0.2

Version 2.2.3
=============

* Reduced the number of call to doveadm

You need to setup a new worker :

1. Create a new supervisord config (``/etc/supervisor/conf.d/modoboa-base-worker.conf`` by default) :

.. sourcecode:: ini

   [program:modoboa-base-worker]
   autostart=true
   autorestart=true
   command={%python env path%} {% manage.py instance path%} rqworker modoboa
   directory={%modoboa home dir%}
   user=%{modoboa user}
   numprocs=1
   stopsignal=TERM

``python env path`` : Python executable located in your virtual environment created for modoboa.
You will find it here  ``/srv/modoboa/venv/bin/python`` by default.
``manage.py instance path``: Path to manage.py of your modoboa instance.
You will find it here : ``/srv/modoboa/instance/manage.py``by default.
``Modoboa home dir``: Home dir of the user running modooba.
You will find it here ``/srv/modoboa/`` by default.
``modoboa user`` : User managing dkim signing (modoboa by default).

You can help you with ``/etc/supervisor/conf.d/policyd.conf`` (by default).

Then restart supervisor. ``#> supervisorctl reread && supervisorctl update`` on Debian.

2. Update the RQ_QUEUES section bellow the ``#REDIS`` section:

.. sourcecode:: python

   # RQ
   RQ_QUEUES = {
      ...
      },
      'modoboa': {
         'HOST': REDIS_HOST,
         'PORT': REDIS_PORT,
         'DB': 0,
      },
   }

3. Add the CACHE section bellow the ``# RQ`` one:

.. sourcecode:: python

   # CACHE
   CACHES = {
      "default": {
         "BACKEND": 'django.core.cache.backends.redis.RedisCache',
         "LOCATION": REDIS_URL
      }
   }


Version 2.2.0
=============

.. note::
   If you use the installer to perform the upgrade, you NEED to update it.
   See above for instructions.
   After updating the installer and modoboa with it,
   you only need to edit ``urls.py`` and ``settings.py``

* Django has been updated to 4.2LTS. Please upgrade all your extensions alongside modoboa
* Support for Python 3.7 has been dropped, minimum Python version is now 3.8
* Support for Postgres 11 has been dropped, minimum Postgres version is now 12

You need to change the first line in ``urls.py`` and replace `url` with `path` (in
``/srv/modoboa/instance/instance/urls.py`` by default):

.. sourcecode:: python

   # from django.conf.urls import include, url
   from django.urls import include, path

   urlpatterns = [
      path(r'', include('modoboa.urls')),
   ]


If you use Postgresql, you need to install pyscopg3+:

.. sourcecode:: bash

   pip install psycopg[binary]>=3.1

RQ has been added. This should replace the use of cron jobs in the future.
For now, only ``manage_dkim_keys`` has been migrated. This will make the dkim
key generation asynchronous but the task will be started as soon as the generation
is required.

Follow these instructions to perform the update in case you used supervisord for the
installation (this apply if you used ``modoboa-installer``):

1. Edit settings.py (``/srv/modoboa/instance/instance/settings.py`` by default) and add:

.. sourcecode:: python

   INSTALLED_APPS = (
       ...,
       'django_rq',
   )

and add the RQ section bellow the ``#REDIS`` section:

.. sourcecode:: python

   # RQ
   RQ_QUEUES = {
      'dkim': {
         'HOST': REDIS_HOST,
         'PORT': REDIS_PORT,
         'DB': 0,
      },
   }

Then by default you will need to restart ``uwsgi`` service (``systemctl restart uwsgi`` on Debian).

2. Create a new supervisord config (``/etc/supervisor/conf.d/modoboa-worker.conf`` by default) :

.. sourcecode:: ini

   [program:modoboa-worker]
   autostart=true
   autorestart=true
   command={%python env path%} {% manage.py instance path%} rqworker dkim
   directory={%modoboa home dir%}
   user=%{dkim manager user}
   numprocs=1
   stopsignal=TERM

``python env path`` : Python executable located in your virtual environment created for modoboa.
You will find it here  ``/srv/modoboa/venv/bin/python`` by default.
``manage.py instance path``: Path to manage.py of your modoboa instance.
You will find it here : ``/srv/modoboa/instance/manage.py``by default.
``Modoboa home dir``: Home dir of the user running modooba.
You will find it here ``/srv/modoboa/`` by default.
``dkim manager user`` : User managing dkim signing (opendkim by default).

You can help you with ``/etc/supervisor/conf.d/policyd.conf`` (by default).

Then restart supervisor. ``#> supervisorctl reread && supervisorctl update`` on Debian.

Admins now have the option to setup a send-only mailbox.

Send-only mailboxes do not have access to IMAP.
You need to change your dovecot configuration to enable it.

.. note::

   modoboa-webmail may not work with send-only user for now.

If you use ``Postgres``:
Change ``user_query`` and ``password_query`` in ``/etc/dovecot/dovecot-sql.conf.ext``::

  user_query = SELECT '%{home_dir}/%%d/%%n' AS home, %mailboxes_owner_uid as uid, %mailboxes_owner_gid as gid, '*:bytes=' || mb.quota || 'M' AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN core_user u ON u.id=mb.user_id WHERE (mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) AND mb.address='%%n' AND dom.name='%%d'

  password_query = SELECT email AS user, password, '%{home_dir}/%%d/%%n' AS userdb_home, %mailboxes_owner_uid AS userdb_uid, %mailboxes_owner_gid AS userdb_gid, CONCAT('*:bytes=', mb.quota, 'M') AS userdb_quota_rule FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE (mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3')) AND email='%%u' AND is_active AND dom.enabled


You basically simply need to add ``(mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) AND`` for ``user_query`` after ``WHERE`` and ``(mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3')) AND`` for ``password_query`` after ``WHERE``.


If you use ``MySQL``:
Change ``user_query`` and ``password_query`` in ``/etc/dovecot/dovecot-sql-master.ext``::

  user_query = SELECT '%{home_dir}/%%d/%%n' AS home, %mailboxes_owner_uid as uid, %mailboxes_owner_gid as gid, CONCAT('*:bytes=', mb.quota, 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN core_user u ON u.id=mb.user_id WHERE (mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) AND mb.address='%%n' AND dom.name='%%d'

  password_query = SELECT email AS user, password, '%{home_dir}/%%d/%%n' AS userdb_home, %mailboxes_owner_uid AS userdb_uid, %mailboxes_owner_gid AS userdb_gid, CONCAT('*:bytes=', mb.quota, 'M') AS userdb_quota_rule FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE (mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3')) AND u.email='%%u' AND u.is_active=1 AND dom.enabled=1

You basically simply need to add ``(mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) AND`` for ``user_query`` after ``WHERE`` and ``(mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3'))`` for ``password_query`` after ``WHERE``.

Version 2.1.0
=============

.. warning::

   For this particular version, it is really important that you apply
   new migrations **AFTER** the following instructions. If you don't,
   you'll get into trouble...

The ``modoboa-dmarc``, ``modoboa-pdfcredentials`` and ``modoboa-imapmigration``
plugins have been merged into the core.

Add ``'django_rename_app,'`` To ``INSTALLED_APPS``:

.. sourcecode:: python

   INSTALLED_APPS = (
   ...,
   'django_rename_app',
   )

Add ``'modoboa.dmarc'``, ``'modoboa.pdfcredentials'`` and ``'modoboa.imap_migration'``
to ``MODOBOA_APPS``:

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
      'modoboa.policyd',
      'modoboa.maillog',
      'modoboa.dmarc',
      'modoboa.pdfcredentials',
      'modoboa.imap_migration',
   )

And remove any reference to ``'modoboa_dmarc'``, ``'modoboa_pdfcredentials'`` or ``'modoboa_imap_migration'``
in this same variable.

You need to add ``'modoboa.imap_migration.auth_backends.IMAPBackend',`` at the end of ``AUTHENTICATION_BACKENDS``:

.. sourcecode:: python

   AUTHENTICATION_BACKENDS = (
      'django.contrib.auth.backends.ModelBackend',
      'modoboa.imap_migration.auth_backends.IMAPBackend',
   )

.. note::
   It won't affect login if you don't use ``imap_migration`` feature.
   It is therefor highly recommended to add this authentication backend.

After upgrading modoboa, run the following commands from your virtual environment:

.. sourcecode:: bash

   > python manage.py rename_app modoboa_dmarc dmarc
   > python manage.py rename_app modoboa_imap_migration imap_migration


Version 2.0.4
=============

The following modifications must be applied to the :file:`settings.py` file:

* Add ``'modoboa.core.context_processors.new_admin_url',`` at the end of `context_processors` list:

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
                   'modoboa.core.context_processors.new_admin_url',
               ],
               'debug': False,
           },
       },
   ]


* Add the following variable:

.. sourcecode:: python

   PID_FILE_STORAGE_PATH = '/var/run'

* Update ``LOGGING`` variable to define an address for ``syslog-auth`` handler:

.. sourcecode:: python

   'syslog-auth': {
       'class': 'logging.handlers.SysLogHandler',
       'facility': SysLogHandler.LOG_AUTH,
       'formatter': 'syslog',
       'address': '/dev/log'
   },


* You now have the possibility to customize the url of the new-admin interface.
   To do so please head up to :ref:`the custom configuration chapter <customization>` (advanced user).

* Add ``DEFAULT_THROTTLE_RATES`` to ``REST_FRAMEWORK``:

.. sourcecode:: python

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
         'modoboa.core.drf_authentication.JWTAuthenticationWith2FA',
         'rest_framework.authentication.TokenAuthentication',
         'rest_framework.authentication.SessionAuthentication',
      ),
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
      'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
   }

* You can edit the ``DEFAULT_THROTTLE_RATES`` to whatever value suits you.
   - `user` is for every endpoint, it is per user or per ip if not logged.
   - `ddos` is per api endpoint and per user or per ip if not logged.
   - `ddos_lesser` is for per api endpoint and per user or per ip if not logged. This is for api endpoint that are lighter.
   - `login` the number of time an ip can attempt to log. The counter will reset on login success.
   - `password_` is for the recovery, it is divided per step in the recovery process.


Version 2.0.3
=============

Update the new following setting in the :file:`settings.py` file:

.. sourcecode:: python

   DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


Version 2.0.0
=============

Add ``drf_spectacular`` and ``phonenumber_field`` to ``INSTALLED_APPS``
in the :file:`settings.py` file, as follows:

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
       'drf_spectacular',
       'phonenumber_field',
       'django_otp',
       'django_otp.plugins.otp_totp',
       'django_otp.plugins.otp_static',
   )

Modify the ``REST_FRAMEWORK`` setting as follows:

.. sourcecode:: python

   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'modoboa.core.drf_authentication.JWTAuthenticationWith2FA',
           'rest_framework.authentication.TokenAuthentication',
           'rest_framework.authentication.SessionAuthentication',
       ),
       'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
       'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
   }

Add the new following settings:

.. sourcecode:: python

   SPECTACULAR_SETTINGS = {
       'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
       'TITLE': 'Modoboa API',
       'VERSION': None,
       'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
   }

   PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'

   DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

Migration issue for Postgres/OpenDKIM users
-------------------------------------------

The `migration will probably fail <https://github.com/modoboa/modoboa/issues/2508>`_ because of the
additional view created for OpenDKIM.

To make it work, you first need to drop the view:

.. sourcecode:: bash

   $ sudo su - postgres
   $ psql
   psql (12.10 (Ubuntu 12.10-0ubuntu0.20.04.1))
   Type "help" for help.

   postgres=# \c modoboa
   You are now connected to database "modoboa" as user "postgres".
   modoboa-# \d+ dkim
                                         View "public.dkim"
         Column      |          Type          | Collation | Nullable | Default | Storage  | Description
   ------------------+------------------------+-----------+----------+---------+----------+-------------
    id               | integer                |           |          |         | plain    |
    domain_name      | character varying(100) |           |          |         | extended |
    private_key_path | character varying(254) |           |          |         | extended |
    selector         | character varying(30)  |           |          |         | extended |
   View definition:
    SELECT admin_domain.id,
       admin_domain.name AS domain_name,
       admin_domain.dkim_private_key_path AS private_key_path,
       admin_domain.dkim_key_selector AS selector
      FROM admin_domain
     WHERE admin_domain.enable_dkim;

   modoboa=# drop view dkim;
   DROP VIEW

Then, run the migration as usual:

.. sourcecode:: bash

   python manage.py migrate

Finally, recreate the view:

.. sourcecode:: bash

   modoboa=# CREATE OR REPLACE VIEW dkim AS
   modoboa-#  SELECT admin_domain.id,
   modoboa-#     admin_domain.name AS domain_name,
   modoboa-#     admin_domain.dkim_private_key_path AS private_key_path,
   modoboa-#     admin_domain.dkim_key_selector AS selector
   modoboa-#    FROM admin_domain
   modoboa-#   WHERE admin_domain.enable_dkim;
   CREATE VIEW
   modoboa=# grant select on dkim to opendkim;
   GRANT

New admin interface
-------------------

This new release brings a new admin interface written with Vue.js framework.
It is a work in progress and all features are not yet implemented - i.e.
extensions integration - but you could give it a try. It uses a new API
version but the old one is still available.

You will need to copy the frontend files in the folder you specified in your
web server configuration. If you used the installer, the folder should be
``/srv/modoboa/instance/frontend``:

.. sourcecode:: bash

   mkdir /srv/modoboa/instance/frontend
   cp -r /srv/modoboa/env/lib/pythonX.X/site-packages/modoboa/frontend_dist/* /srv/modoboa/instance/frontend

Then, edit the :file:`/srv/modoboa/instance/frontend/config.json`
and update the ``API_BASE_URL`` setting according to the hostname of your server:

.. sourcecode:: json

   {
       "API_BASE_URL": "https://<hostname of your server>/api/v2"
   }

Finally, update the configuration of your web server to serve the frontend
files. For NGINX, you should add the following in the ``server`` block:

.. sourcecode:: nginx

   location ^~ /new-admin {
       alias  /srv/modoboa/instance/frontend/;
       index  index.html;

       expires -1;
       add_header Pragma "no-cache";
       add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";

       try_files $uri $uri/ /index.html = 404;
   }

Version 1.17.0
==============

Modoboa now supports Two-Factor authentication using TOTP
applications.

To enable it, install the following new requirement in your
virtualenv:

.. sourcecode:: bash

   (env)> pip install django-otp qrcode

Then, open the :file:`settings.py` file and add ``django_otp``
packages to ``INSTALLED_APPS``:

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
       'django_otp',
       'django_otp.plugins.otp_totp',
       'django_otp.plugins.otp_static',
   )

Add new middlewares to ``MIDDLEWARE``. It has to be after the SessionMiddleware and before the CommonMiddleware:

.. sourcecode:: python

   MIDDLEWARE = (
       'x_forwarded_for.middleware.XForwardedForMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.locale.LocaleMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'django_otp.middleware.OTPMiddleware',
       'modoboa.core.middleware.TwoFAMiddleware',
       'django.contrib.messages.middleware.MessageMiddleware',
       'django.middleware.clickjacking.XFrameOptionsMiddleware',
       'modoboa.core.middleware.LocalConfigMiddleware',
       'modoboa.lib.middleware.AjaxLoginRedirect',
       'modoboa.lib.middleware.CommonExceptionCatcher',
       'modoboa.lib.middleware.RequestCatcherMiddleware',
   )

And add the following new setting:

.. sourcecode:: python

   # 2FA

   OTP_TOTP_ISSUER = "<your server hostname here>"


Version 1.16.0
==============

A new :ref:`policy daemon <policy_daemon>` has been added.

Make sure to have a Redis instance running on your server.

Add ``'modoboa.policyd'`` to ``MODOBOA_APPS``:

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
      'modoboa.policyd'
   )

Add the following settings to your ``settings.py`` file:

.. sourcecode:: python

   REDIS_HOST = '<IP or hostname here>'
   REDIS_PORT = 6379
   REDIS_QUOTA_DB = 0
   REDIS_URL = 'redis://{}:{}/{}'.format(REDIS_HOST, REDIS_PORT, REDIS_QUOTA_DB)

Or, if Redis listen on unix socket and you are not using the Modoboa installer:

.. sourcecode:: python

   REDIS_HOST = '/path/to/redis/socket'
   REDIS_PORT = 6379
   REDIS_QUOTA_DB = 0
   REDIS_URL = 'unix://{}?db={}'.format(REDIS_HOST, REDIS_QUOTA_DB)

Once done, you can start the policy daemon using the following commands:

.. sourcecode:: bash

   > python manage.py policy_daemon

Don't forget to configure :ref:`_policyd_config <postfix>` if you want
to use this feature.

The ``modoboa-stats`` plugin has been merged into the core.

Add ``'modoboa.maillog'`` to ``MODOBOA_APPS``:

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
      'modoboa.policyd',
      'modoboa.maillog',
   )

And remove any reference to ``modoboa_stats`` in this same variable.

Version 1.15.0
==============

This version drops Python 2 support so don't forget to update all the
extensions you use.

.. warning::

   If you upgrade an existing python 2 installation, you will need to
   create a new Python 3 virtual environment. You can remove the
   existing virtual environment and replace it by the new one so you
   won't have to modify your configuration files.

Add the following new setting:

.. sourcecode:: python

   DISABLE_DASHBOARD_EXTERNAL_QUERIES = False

Reload uwsgi/gunicorn/apache depending on your setup.

Finally, Make sure to use root privileges and run the following
command:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <directory>

Then, reload postfix.


Version 1.14.0
==============

This release introduces an optional LDAP synchronization process. If
you want to use it, please follow the :ref:`dedicated procedure <ldap_sync>`.

Version 1.13.1
==============

Upgrade postfix maps files as follows:

.. sourcecode:: bash

   > python manage.py generate_postfix_maps --destdir <path> --force-overwrite


Version 1.13.0
==============

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

Version 1.10.0
==============

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

Version 1.9.0
=============

If you want to manage inactive accounts, look at :ref:`inactive_accounts`.

Version 1.8.3
=============

Edit the :file:`settings.py` file and replace the following line:

.. sourcecode:: python

   BASE_DIR = os.path.dirname(os.path.dirname(__file__))

by:

.. sourcecode:: python

   BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

Version 1.8.0
=============

Modoboa now relies on `Django's builtin password validation system
<https://docs.djangoproject.com/en/1.10/topics/auth/passwords/#module-django.contrib.auth.password_validation>`_
to validate user passwords, instead of ``django-passwords``.

Remove ``django-passwords`` from your system:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
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

Version 1.7.2
=============

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


Version 1.7.1
=============

If you used 1.7.0 for a fresh installation, please run the following commands:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
   > source <virtuenv_path>/bin/activate
   > cd <modoboa_instance_dir>
   > python manage.py load_initial_data

Version 1.7.0
=============

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

   > sudo -u <modoboa_user> -i bash
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

Version 1.6.1
=============

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


Version 1.6.0
=============

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

Version 1.5.0
=============

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

Version 1.4.0
=============

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

Version 1.3.5
=============

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


Version 1.3.2
=============

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

Version 1.3.0
=============

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

Version 1.2.0
=============

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
