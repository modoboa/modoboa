#############
Configuration
#############

*****************
Online parameters
*****************

FIXME : present the online panel

Throught the *Admin > Configuration* panel, you can customize the way
Modoboa stores mailboxes on the filesystem. Here is the list of
editable parameters with their default value::

Administration application
==========================

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
:ref:`default-conf`.

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

FIXME : per user language

Modoboa is available in english, french, german and spanish. You can choose
which language to use by modifying the ``LANGUAGE_CODE`` variable inside
*settings.py*::

  LANGUAGE_CODE = 'en-US' # English
  # or
  LANGUAGE_CODE = 'fr-FR' # French
  # or
  LANGUAGE_CODE = 'de-DE' # German
  # or
  LANGUAGE_CODE = 'es-ES' # Spanish

You can also specify your time zone by modifying the ``TIME_ZONE``
variable. For example::

  TIME_ZONE = 'Europe/Paris'

