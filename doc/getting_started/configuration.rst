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

