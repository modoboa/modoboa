#################
Moving to Modoboa
#################

You have an existing platform and you'd like to move to Modoboa, the
following tools could help you.

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

   > sudo -u <modoboa_user> -i
   > source <virtualenv_path>/bin/activate
   > cd <modoboa_instance_dir>
   > python manage.py modo import <your file>

Available options can be listed using the following command:

.. sourcecode:: bash

   > python manage.py modo import -h
