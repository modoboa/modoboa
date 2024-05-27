#################
Moving to Modoboa
#################

You have an existing platform and you'd like to move to Modoboa, the
following tools could help you.

Using IMAP protocol
===================

.. _imap:

`Modoboa <https://modoboa.org/>`_ provides a way to transfer accounts
hosted on a different platform/provider to your personal server using
the IMAP protocol and a tool called `OfflineIMAP
<https://www.offlineimap.org/doc/installation.html>`_.

It works as follows:

* You first declare what needs to be migrated, basically the domain(s) you own and where they can be found. By doing that, you'll allow accounts hosted on the platform/provider you're migrating from to log into your Modoboa server
* The first time an old account (one coming from your previous provider) successfuly log into Modoboa, a dedicated migration task is created
* On a regular basis (every hour generally), a cron job is responsible for generating an OfflineIMAP configuration file including instructions to migrate all declared migrations and lauching OfflineIMAP to start/continue migrations

.. warning::

   As you probably already understood, you can't migrate all your
   accounts at the same time since you don't know their corresponding
   password (most of the time). Every account migration must be
   started by the account's owner.

Configuration
-------------

Modoboa won'thandle the installation of OfflineIMAP so you
need to do it on your own. The following `instructions
<https://www.offlineimap.org/doc/quick_start.html>`_ will help you.

Once done, *the new admin interface (v2)* will let you:

* define the neccessary information to `connect to your old platform/provider <providers>`_
* define `what is to be migrated <migrations>`_ (ie. the accounts)
* customize the behaviour of OfflineIMAP : go to 'Parameters > Imap Migration' from the left menu

.. warning::

   **Auto create domain** option must be enabled to make this feature
    work. Go to 'Parameters > Administration > Mailboxes' and check if
    it's the case.

To generate an OfflineIMAP configuration file, run the following command:

.. sourcecode:: bash

   > python manage.py generate_offlineimap_config

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

.. _providers:

Providers
---------

A provider represents an IMAP server that hosts one or several domains
you own. It includes connection information (network address, port,
etc.) and a list of hosted domain.

For each domain you declare, you must provide its name. Modoboa will
then create a local domain with the exact same name if needed (ie. if
it does not exist yet) the first time it migrates an account.

Optionaly, you have the possibility to rename a domain (for example:
domain.com -> domain.net) by providing a value to the 'Local domain'
field.

.. _migrations:

Migrations
----------

Migrations are automatically created, you don't need to do it.

The first time an account of your old platform successfuly log into
Modoboa (using old credentials), a local account and a migration task
will be created.

.. warning::

   In case of domain renaming as described in `Providers <providers>`_,
   users must use the new email address as username for next connection
   attempts.

SuperAdmins can monitor running migrations and stop/delete them from
the `IMAP Migration` section (left menu).


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
