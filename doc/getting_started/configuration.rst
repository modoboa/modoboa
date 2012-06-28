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

*admin* application parameters
==============================

The *admin* application exposes several parameters, mainly to control
how mailboxes are created and how messages are stored on the file
system.

Default values are presented below::

  The authentication type
  AUTHENTICATION_TYPE = Local

  Does Modoboa need to handle the creation of directories on the file system?
  CREATE_DIRECTORIES = Yes

  Where Modoboa stores mailboxes
  STORAGE_PATH = /var/vmail

  Which user:group Modoboa uses to assign permissions on mailboxes
  VIRTUAL_UID = vmail
  VIRTUAL_GID = vmail

  Which format is used to store messages in a mailbox
  MAILBOX_TYPE = maildir

  If maildir is in use, tells Modoboa that mailbox content is under a
  potential sub-directory
  MAILDIR_ROOT = .maildir

  The encryption method used to store passwords
  PASSWORD_SCHEME = crypt

  The number of displayed items per page for listing pages
  ITEMS_PER_PAGE = 30

******************
Host configuration
******************

.. note::

  This section is only relevant when the ``CREATE_DIRECTORIES``
  parameter is set to ``Yes``.

To let Modoboa create mailboxes and store emails on the filesystem,
you must create a group and a user (UNIX ones). There is only one
group/user needed because we are in a virtual hosting configuration
(ie. users with non-UNIX accounts). 

The following examples are based on the default values presented in
:ref:`admin-params`.

For example, create a vmail group::

  $ groupadd vmail

Then create a vmail user::

  $ useradd -g vmail -d /var/vmail -m vmail

At last, the system user used to run modoboa will need permissions to
manipulate directories in vmail's homedir. To do so, edit the
*/etc/sudoers* file and add the following inside::

  <user_that_runs_modoboa> ALL=(vmail) NOPASSWD: ALL

**********************
Time zone and language
**********************

Modoboa is available in english, french, german and spanish.

To specify the default language to use, edit the *settings.py* file
and modify the ``LANGUAGE_CODE`` variable::

  LANGUAGE_CODE = 'en-US' # English
  # or
  LANGUAGE_CODE = 'fr-FR' # French
  # or
  LANGUAGE_CODE = 'de-DE' # German
  # or
  LANGUAGE_CODE = 'es-ES' # Spanish

.. note::

  Each user has the possibility to define the language he prefers.

In the same configuration file, specify the timezone to use by
modifying the ``TIME_ZONE`` variable. For example::

  TIME_ZONE = 'Europe/Paris'

***********************
External authentication
***********************

LDAP
====

*Modoboa* supports external LDAP authentication using the following extra components:

* `Python LDAP client <http://www.python-ldap.org/>`_
* `Django LDAP authentication backend <http://pypi.python.org/pypi/django-auth-ldap>`_

If you want to use this feature, you must first install those components::

  $ pip install python-ldap django-auth-ldap

Then, all you have to do is to modify the *settings.py* file:

* Add a new authentication backend to the `AUTHENTICATION_BACKENDS`
  variable, like this::

    AUTHENTICATION_BACKENDS = (
      'django_auth_ldap.backend.LDAPBackend',
      'modoboa.lib.authbackends.SimpleBackend',
      'django.contrib.auth.backends.ModelBackend',
    )

* Set the required parameters to establish the communication with your
  LDAP server, for example::

    import ldap
    from django_auth_ldap.config import LDAPSearch

    AUTH_LDAP_BIND_DN = ""
    AUTH_LDAP_BIND_PASSWORD = ""
    LDAP_USER_BASE = "ou=users,dc=example,dc=com"	
    LDAP_USER_FILTER = "(mail=%(user)s)"
    AUTH_LDAP_USER_SEARCH = LDAPSearch(LDAP_USER_BASE,
        ldap.SCOPE_SUBTREE, LDAP_USER_FILTER)

You will find a detailled documentation `here
<http://packages.python.org/django-auth-ldap/>`_.

Once the authentication is properly configured, the users defined in
your LDAP directory will be able to connect to *Modoboa*, the associated
domain and mailboxes will be automatically created if needed.

Users will also be able to update their LDAP password directly from
Modoboa.

.. note:: 

   Modoboa doesn't provide any synchronization mechanism once a user
   is registered into the database. Any modification done from the
   directory to a user account will not be reported to Modoboa (an
   email address change for example). Currently, the only solution is
   to manually delete the Modoboa record, it will be recreated on the
   next user login.

Available settings
------------------

* ``LDAP_USER_BASE`` : the distinguish name of the search base
* ``LDAP_USER_FILTER`` : the filter used to retrieve users distinguish name
* ``LDAP_PASSWORD_ATTR`` : the attribute used to store the password
  (default: ``userPassword``)
* ``LDAP_ACTIVE_DIRECTORY`` : used to indicate if your directory is an
  Active Directory one (default: ``False``)
