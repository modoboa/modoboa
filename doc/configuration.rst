#############
Configuration
#############

*****************
Online parameters
*****************

Modoboa provides online panels to modify internal parameters. There
are two available levels:

* Application level: global parameters, define how the application
  behaves. Available at *Modoboa > Parameters*

* User level: per user customization. Available at *User > Settings >
  Preferences*

Regardless level, parameters are displayed using tabs, each tab
corresponding to one application.

.. _admin-params:

General parameters
==================

The *admin* application exposes several parameters, they are presented below:

+--------------------+---------------------+-------------------------------+--------------------+
|Name                |Tab                  |Description                    |Default value       |
+====================+=====================+===============================+====================+
|Authentication type |General              |The backend used for           |Local               |
|                    |                     |authentication                 |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Default password    |General              |Scheme used to crypt           |crypt               |
|scheme              |                     |mailbox passwords              |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Rounds              |General              |Number of rounds (only used by |70000               |
|                    |                     |`sha256crypt` and              |                    |
|                    |                     |`sha512crypt`). Must be between|                    |
|                    |                     |1000 and 999999999, inclusive. |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Secret key          |General              |A key used to                  |random value        |
|                    |                     |encrypt users'                 |                    |
|                    |                     |password in sessions           |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Sender address      |General              |Email address used to send     |                    |
|                    |                     |notifications.                 |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Enable communication|General              |Enable communication with      |yes                 |
|                    |                     |Modoboa public API             |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Check new versions  |General              |Automatically checks if a newer|yes                 |
|                    |                     |version is available           |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Send statistics     |General              |Send statistics to Modoboa     |yes                 |
|                    |                     |public API (counters and used  |                    |
|                    |                     |extensions)                    |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Top notifications   |General              |Interval between two top       |30                  |
|check interval      |                     |notification checks (in        |                    |
|                    |                     |seconds)                       |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Maximum log record  |General              |The maximum age in             |365                 |
|age                 |                     |days of a log record           |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Items per page      |General              |Number of displayed            |30                  |
|                    |                     |items per page                 |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Default top         |General              |The default                    |userprefs           |
|redirection         |                     |redirection used               |                    |
|                    |                     |when no application            |                    |
|                    |                     |is specified                   |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Enable MX checks    |Admin                |Check that every domain has a  |yes                 |
|                    |                     |valid MX record                |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Valid MXs           |Admin                |A list of IP or network address|                    |
|                    |                     |every MX should match. A       |                    |
|                    |                     |warning will be sent if a      |                    |
|                    |                     |record does not respect this   |                    |
|                    |                     |it.                            |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Enable DNSBL checks |Admin                |Check every domain against     |yes                 |
|                    |                     |major DNSBL providers          |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|DKIM keys storage   |Admin                |Path to a directory where DKIM |                    |
|directory           |                     | generated keys will be stored |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Default DKIM key    |Admin                |The default size (in bits) for |2048                |
|length              |                     |new keys                       |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Handle mailboxes on |Admin                |Rename or remove               |no                  |
|filesystem          |                     |mailboxes on the               |                    |
|                    |                     |filesystem when they           |                    |
|                    |                     |get renamed or                 |                    |
|                    |                     |removed within                 |                    |
|                    |                     |Modoboa                        |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Mailboxes owner     |Admin                |The UNIX account who           |vmail               |
|                    |                     |owns mailboxes on              |                    |
|                    |                     |the filesystem                 |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Default domain quota|Admin                |Default quota (in MB) applied  |0                   |
|                    |                     |to freshly created domains with|                    |
|                    |                     |no value specified. A value of |                    |
|                    |                     |0 means no quota.              |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Automatic account   |Admin                |When a mailbox is              |no                  |
|removal             |                     |removed, also remove           |                    |
|                    |                     |the associated                 |                    |
|                    |                     |account                        |                    |
+--------------------+---------------------+-------------------------------+--------------------+
|Automatic           |Admin                |Create a domain and a mailbox  |yes                 |
|domain/mailbox      |                     |when an account is             |                    |
|creation            |                     |automatically created          |                    |
|                    |                     |                               |                    |
+--------------------+---------------------+-------------------------------+--------------------+

.. note::

   If you are not familiar with virtual domain hosting, you should
   take a look at `postfix's documentation
   <http://www.postfix.org/VIRTUAL_README.html>`_. This `How to
   <https://help.ubuntu.com/community/PostfixVirtualMailBoxClamSmtpHowto>`_
   also contains useful information.

.. note::

   A random secret key will be generated each time the *Parameters*
   page is refreshed and until you save parameters at least once.

.. note::

   Specific LDAP parameters are also available, see :ref:`LDAP
   authentication <ldap_auth>`.

***********
Media files
***********

Modoboa uses a specific directory to upload files (ie. when the
webmail is in use) or to create ones (ex: graphical statistics). This
directory is named ``media`` and is located inside modoboa's
installation directory (called ``modoboa_site`` in this
documentation).

To work properly, the system user which runs modoboa (``www-data``,
``apache``, whatever) must have write access to this directory.


*************
Customization
*************

Custom logo
===========

You have the possibility to use a custom logo instead of the default
one on the login page.

To do so, open the :file:`settings.py` file and add a
``MODOBOA_CUSTOM_LOGO`` variable. This variable must contain the
relative URL of your logo under ``MEDIA_URL``. For example::

  MODOBOA_CUSTOM_LOGO = os.path.join(MEDIA_URL, "custom_logo.png")

Then copy your logo file into the directory indicated by
``MEDIA_ROOT``.

******************
Host configuration
******************

.. note::

  This section is only relevant when Modoboa handles mailboxes
  renaming and removal from the filesystem.

To manipulate mailboxes on the filesystem, you must allow the user who
runs Modoboa to execute commands as the user who owns mailboxes.

To do so, edit the :file:`/etc/sudoers` file and add the following inside::

  <user_that_runs_modoboa> ALL=(<mailboxes owner>) NOPASSWD: ALL

Replace values between ``<>`` by the ones you use.

.. _timezone_lang:

**********************
Time zone and language
**********************

Modoboa is available in many languages.

To specify the default language to use, edit the :file:`settings.py` file
and modify the ``LANGUAGE_CODE`` variable::

  LANGUAGE_CODE = 'fr' # or 'en' for english, etc.

.. note::

  Each user has the possibility to define the language he prefers.

In the same configuration file, specify the timezone to use by
modifying the ``TIME_ZONE`` variable. For example::

  TIME_ZONE = 'Europe/Paris'

*******************
Sessions management
*******************

Modoboa uses `Django's session framework
<https://docs.djangoproject.com/en/dev/topics/http/sessions/?from=olddocs>`_
to store per-user information.

Few parameters need to be set in the :file:`settings.py` configuration
file to make Modoboa behave as expected::

  SESSION_EXPIRE_AT_BROWSER_CLOSE = False # Default value

This parameter is optional but you must ensure it is set to ``False``
(the default value).

The default configuration file provided by the ``modoboa-admin.py``
command is properly configured.

**********************
Logging authentication
**********************

To trace login attempts to the web interface, Modoboa uses python
`SysLogHandler <https://docs.python.org/3/library/logging.handlers.html#logging.handlers.SysLogHandler>`_
so you can see them in your syslog authentication log file
(`/var/log/auth.log` in most cases).

Depending on your configuration, you may have to edit the :file:`settings.py` file
and add `'address': '/dev/log'` to the logging section::

    'syslog-auth': {
        'class': 'logging.handlers.SysLogHandler',
        'facility': SysLogHandler.LOG_AUTH,
        'address': '/dev/log',
        'formatter': 'syslog'
    },

***********************
External authentication
***********************

.. _ldap_auth:

LDAP
====

Modoboa supports external LDAP authentication using the following extra components:

* `Python LDAP client <http://www.python-ldap.org/>`_
* `Django LDAP authentication backend <http://pypi.python.org/pypi/django-auth-ldap>`_

If you want to use this feature, you must first install those components::

  $ pip install python-ldap django-auth-ldap

Then, all you have to do is to modify the :file:`settings.py` file. Add a
new authentication backend to the `AUTHENTICATION_BACKENDS` variable,
like this::

    AUTHENTICATION_BACKENDS = (
      'modoboa.lib.authbackends.LDAPBackend',
      'django.contrib.auth.backends.ModelBackend',
    )

Finally, go to *Modoboa > Parameters > General* and set *Authentication
type* to LDAP.

From there, new parameters will appear to let you configure the way
Modoboa should connect to your LDAP server. They are described just below:

+--------------------+---------------------------------+--------------------+
|Name                |Description                      |Default value       |
+====================+=================================+====================+
|Server address      |The IP address of                |localhost           |
|                    |the DNS name of the              |                    |
|                    |LDAP server                      |                    |
+--------------------+---------------------------------+--------------------+
|Server port         |The TCP port number              |389                 |
|                    |used by the LDAP                 |                    |
|                    |server                           |                    |
+--------------------+---------------------------------+--------------------+
|Use a secure        |Use an SSL/TLS                   |no                  |
|connection          |connection to access             |                    |
|                    |the LDAP server                  |                    |
+--------------------+---------------------------------+--------------------+
|Authentication      |Choose the                       |Direct bind         |
|method              |authentication                   |                    |
|                    |method to use                    |                    |
+--------------------+---------------------------------+--------------------+
|User DN template    |The template used to             |                    |
|(direct bind mode)  |construct a user's               |                    |
|                    |DN. It should                    |                    |
|                    |contain one                      |                    |
|                    |placeholder                      |                    |
|                    |(ie. ``%(user)s``)               |                    |
+--------------------+---------------------------------+--------------------+
|Bind BN             |The distinguished                |                    |
|                    |name to use when                 |                    |
|                    |binding to the LDAP              |                    |
|                    |server. Leave empty              |                    |
|                    |for an anonymous                 |                    |
|                    |bind                             |                    |
+--------------------+---------------------------------+--------------------+
|Bind password       |The password to use              |                    |
|                    |when binding to the              |                    |
|                    |LDAP server (with                |                    |
|                    |'Bind DN')                       |                    |
+--------------------+---------------------------------+--------------------+
|Search base         |The distinguished                |                    |
|                    |name of the search               |                    |
|                    |base                             |                    |
+--------------------+---------------------------------+--------------------+
|Search filter       |An optional filter string        |(mail=%(user)s)     |
|                    |(e.g. '(objectClass=person)'). In|                    |
|                    |order to be valid, it must be    |                    |
|                    |enclosed in parentheses.         |                    |
+--------------------+---------------------------------+--------------------+
|Password attribute  |The attribute used               |userPassword        |
|                    |to store user                    |                    |
|                    |passwords                        |                    |
+--------------------+---------------------------------+--------------------+
|Active Directory    |Tell if the LDAP                 |no                  |
|                    |server is an Active              |                    |
|                    |Directory one                    |                    |
+--------------------+---------------------------------+--------------------+
|Administrator groups|Members of those LDAP Posix      |                    |
|                    |groups will be created ad domain |                    |
|                    |administrators. Use ';'          |                    |
|                    |characters to separate groups.   |                    |
+--------------------+---------------------------------+--------------------+
|Group type          |The type of group used by your   |PosixGroup          |
|                    |LDAP directory.                  |                    |
|                    |                                 |                    |
|                    |                                 |                    |
+--------------------+---------------------------------+--------------------+
|Groups search base  |The distinguished name of the    |                    |
|                    |search base used to find groups  |                    |
|                    |                                 |                    |
|                    |                                 |                    |
+--------------------+---------------------------------+--------------------+
|Domain/mailbox      |Automatically create a domain and|yes                 |
|creation            |a mailbox when a new user is     |                    |
|                    |created just after the first     |                    |
|                    |successful authentication. You   |                    |
|                    |will generally want to disable   |                    |
|                    |this feature when the relay      |                    |
|                    |domains extension is in use      |                    |
+--------------------+---------------------------------+--------------------+


If you need additional parameters, you will find a detailled
documentation `here <http://packages.python.org/django-auth-ldap/>`_.

Once the authentication is properly configured, the users defined in
your LDAP directory will be able to connect to Modoboa, the associated
domain and mailboxes will be automatically created if needed.

The first time a user connects to Modoboa, a local account is created
if the LDAP username is a valid email address. By default, this
account belongs to the *SimpleUsers* group and it has a mailbox.

To automatically create domain administrators, you can use the
**Administrator groups** setting. If a LDAP user belongs to one the
listed groups, its local account will belong to the *DomainAdmins*
group. In this case, the username is not necessarily an email address.

Users will also be able to update their LDAP password directly from
Modoboa.

.. note::

   Modoboa doesn't provide any synchronization mechanism once a user
   is registered into the database. Any modification done from the
   directory to a user account will not be reported to Modoboa (an
   email address change for example). Currently, the only solution is
   to manually delete the Modoboa record, it will be recreated on the
   next user login.

.. _smtp_auth:

SMTP
====

It is possible to use an existing SMTP server as an authentication
source. To enable this feature, edit the :file:`settings.py` file and
change the following setting:

.. sourcecode:: python

   AUTHENTICATION_BACKENDS = (
       'modoboa.lib.authbackends.SMTPBackend',
       'django.contrib.auth.backends.ModelBackend',
   )

SMTP server location can be customized using the following settings:

.. sourcecode:: python

   AUTH_SMTP_SERVER_ADDRESS = 'localhost'
   AUTH_SMTP_SERVER_PORT = 25
   AUTH_SMTP_SECURED_MODE = None  # 'ssl' or 'starttls' are accepted


.. ldap_sync::

********************
LDAP synchronization
********************

Modoboa can synchronize accounts with an LDAP directory (tested with
OpenLDAP) but this feature is not enabled by default. To activate it,
add ``modoboa.ldapsync`` to ``MODOBOA_APPS`` in the
:file:`settings.py` file::

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
        'modoboa.ldapsync',
    )

and enable it from the admin panel.

.. warning::

   Make sure to install additional :ref:`requirements <ldap_auth>`
   otherwise it won't work.

The following parameters are available and must be filled::

+--------------------+---------------------------------+--------------------+
|Name                |Description                      |Default value       |
+====================+=================================+====================+
|Enable LDAP         |Control LDAP synchronization     |no                  |
|synchronization     |state                            |                    |
|                    |                                 |                    |
+--------------------+---------------------------------+--------------------+
|Bind DN             |The DN of a user with write      |                    |
|                    |permission to create/update      |                    |
|                    |accounts                         |                    |
+--------------------+---------------------------------+--------------------+
|Bind password       |The associated password          |                    |
|                    |                                 |                    |
|                    |                                 |                    |
+--------------------+---------------------------------+--------------------+
|Account DN template |The template used to build       |                    |
|                    |account DNs (must contain a      |                    |
|                    |%(user)s placeholder             |                    |
+--------------------+---------------------------------+--------------------+


********************
Database maintenance
********************

Cleaning the logs table
=======================

Modoboa logs administrator specific actions into the database. A
clean-up script is provided to automatically remove oldest
records. The maximum log record age can be configured through the
online panel.

To use it, you can setup a cron job to run every night::

  0 0 * * * <modoboa_site>/manage.py cleanlogs
  #
  # Or like this if you use a virtual environment:
  # 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py cleanlogs

Cleaning the session table
==========================

Django does not provide automatic purging. Therefore, it's your job to
purge expired sessions on a regular basis.

Django provides a sample clean-up script: ``django-admin.py
clearsessions``. That script deletes any session in the session table
whose ``expire_date`` is in the past.

For example, you could setup a cron job to run this script every night::

  0 0 * * * <modoboa_site>/manage.py clearsessions
  #
  # Or like this if you use a virtual environment:
  # 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py clearsessions

.. _inactive_accounts:

Cleaning inactive accounts
==========================

Thanks to :ref:`lastlogin`, it is now possible to monitor inactive
accounts. An account is considered inactive if no login has been
recorded for the last 30 days (this value can be changed through the
admin panel).

A management command is available to disable or delete inactive
accounts. For example, you could setup a cron job to run it every
night::

  0 0 * * * <modoboa_site>/manage.py clean_inactive_accounts
  #
  # Or like this if you use a virtual environment:
  # 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py clean_inactive_accounts

The default behaviour is to disable accounts. You can delete them
using the ``--delete`` option.
