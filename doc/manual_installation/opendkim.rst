########
OpenDKIM
########

Modoboa can generate `DKIM
<https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail>`_ keys for
the hosted domains but it won't sign or check messages. To do that,
you need a dedicated software like `OpenDKIM <http://opendkim.org/>`_.

.. note::

   The cron job in charge of creating DKIM keys must be run using the
   same user than OpenDKIM (ie. opendkim in most cases).

Database
========

Since keys related information is stored in Modoboa's database, you
need to tell OpenDKIM how it can access it.

First, make sure to install the required additional packages on your
system (``libopendbx1-*`` on debian based distributions or ``opendbx-*``
on CentOS, the complete name depends on your database engine).

Then, insert the following SQL view into Modoboa's database:

PostgreSQL
----------

::

   CREATE OR REPLACE VIEW dkim AS (
     SELECT id, name as domain_name, dkim_private_key_path AS private_key_path,
          dkim_key_selector AS selector
     FROM admin_domain WHERE enable_dkim
   );

MySQL/MariaDB
-------------

::
   
   CREATE OR REPLACE VIEW dkim AS (
     SELECT id, name as domain_name, dkim_private_key_path AS private_key_path,
          dkim_key_selector AS selector
     FROM admin_domain WHERE enable_dkim=1
   );

Configuration
=============

You should find OpenDKIM's configuration file at :file:`/etc/opendkim.conf`.

Add the following content to it::

  KeyTable		dsn:<driver>://<user>:<password>@<db host>/<db name>/table=dkim?keycol=id?datacol=domain_name,selector,private_key_path
  SigningTable		dsn:<driver>://<user>:<password>@<db host>/<db name>/table=dkim?keycol=domain_name?datacol=id
  Socket                inet:12345@localhost

Replace values between ``<>`` by yours. Accepted values for ``driver``
are ``pgsql`` or ``mysql``. Make sure the user you specify has read
permission on the view created previously.

If you run a debian based system, make sure to adjust the following
setting in the :file:`/etc/default/opendkim` file::

  SOCKET=inet:12345@localhost

Eventually, reload OpenDKIM.

Postfix integration
===================

Add the following lines to the :file:`/etc/postfix/main.cf` file::

  smtpd_milters = inet:127.0.0.1:12345
  non_smtpd_milters = inet:127.0.0.1:12345
  milter_default_action = accept
  milter_content_timeout = 30s

and reload postfix.
