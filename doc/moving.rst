#################
Moving to Modoboa
#################

You have an existing platform and you'd like to move to Modoboa, the
following tools could help you.

Using IMAP protocol
===================

.. _imap:

`Modoboa <https://modoboa.org/>`_ provides a way to transfer your
account from another provider/server using an IMAP access.

Configuration
-------------

The configuration is done from the admin panel (*Modoboa >
Parameters > IMAP Migration*). And you have a specific tab to configure
your migration that is visible for SuperAdmins.
These settings are only available on the new admin interface.

.. warning::

   You must have enabled **Auto create domain** in modoboa parameters for this extension to work.

This extension can create `OfflineIMAP <https://www.offlineimap.org/doc/installation.html>`_
configuration file with the command:

.. sourcecode:: bash

   > python manage.py generate_offlineimap_config

You then need to setup `OfflineIMAP <https://www.offlineimap.org/doc/quick_start.html>`_.

The synchronization script must be configured to run periodically on
your new server. Since it will copy mailboxes content to its final
destination, filesystem permissions must be respected. To do that, it
must be executed by the user which owns mailboxes (generally
``vmail``).

Here is a configuration example where the script is executed every
hours. You can copy it inside the ``/etc/cron.d/modoboa`` file:

.. sourcecode:: shell

  PYTHON=/srv/modoboa/env/bin/python
  INSTANCE=/srv/modoboa/instance

  0       */1     *       *       *       vmail   cd /srv/vmail && $PYTHON $INSTANCE/manage.py generate_offlineimap_config --output .offlineimaprc && /usr/local/bin/offlineimap > /dev/null 2>&1

Feel free to adapt it.

This will sync back-and-forth user mailbox.

Providers
---------

Mail server can host multiple domains so the provider address
may be different from the domain part of your email address.

Associated domain is the domain part of the email address.
You can leave "Local Domain" blank if you keep the same domain.
This domain will be auto-created if needed.
you must create the domain beforhand if you want to migrate an account
from `user@domain1.tld` to `user@domain2.tld`.


Migrations
----------

Migrations are automatically handled when providers have been configured.
Users use their old credential to log and the account is automatically created.
They shall use the new domain on next logins if a local domain was set in the provider configuration.
If you have installed OfflineIMAP, you may delete the migration to stop mailbox sync.
SuperAdmins may check migrations in the `IMAP Migration` tab.


From postfixadmin
=================

A dedicated command allows you to convert an existing `postfixadmin
<http://postfixadmin.sourceforge.net/>`_ database to a Modoboa
one. Consult the `documentation
<https://github.com/modoboa/modoboa-pfxadmin-migrate>`_ to know more
about the process.

Using CSV files
===============

Modoboa allows you to import any object (domain, domain alias, mailbox
and alias) using a simple CSV file encoded using **UTF8**. Each line
corresponds to a single object and must respect one of the following
format::

  domain; <name: string>; <quota: integer>; <default mailbox quota: integer>; <enabled: boolean>
  domainalias; <name: string>; <targeted domain: string>; <enabled: boolean>
  relaydomain; <name: string>; <target host: string>; <target port: integer>; <service: string>; <enabled: boolean>; <verify recipients: boolean>
  account; <loginname: string>; <password: string>; <first name: string>; <last name: string>; <enabled: boolean>; <group: string>; <address: string>; <quota: integer>; [<domain: string>, ...]
  alias; <address: string>; <enabled: boolean>; <recipient: string>; ...

Boolean fields accept the following values: ``true``, ``1``, ``yes``,
``y`` (case insensitive). Any other value will be evaluated as false.

.. warning::

   The order does matter. Objects are created sequencially so a
   domain must be created before its mailboxes and aliases and a
   mailbox must created before its alias(es).

To actually import such a file:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i bash
   > source <virtualenv_path>/bin/activate
   > cd <modoboa_instance_dir>
   > python manage.py modo import <your file>

Available options can be listed using the following command:

.. sourcecode:: bash

   > python manage.py modo import -h
