.. _dovecot:

#######
Dovecot
#######

Modoboa requires Dovecot 2+ to work so the following documentation is
suitable for this combination.

In this section, we assume dovecot's configuration resides in
:file:`/etc/dovecot`, all pathes will be relative to this directory.

You can find configuration documentation `here <https://doc.dovecot.org/configuration_manual/>`_.

This proposed configuration is the one you can find with modoboa-installer. For up to date configuration, `take a look here <https://github.com/modoboa/modoboa-installer/tree/master/modoboa_installer/scripts/files/dovecot/conf.d>`_

Packages
========

For debian and derivative, recommended packages are::

  apt install dovecot-imapd dovecot-lmtpd dovecot-managesieved dovecot-sieve

Mailboxes
=========

First, edit the :file:`conf.d/10-mail.conf` and set the ``mail_location``
variable::

  # maildir
  mail_location = maildir:~/Maildir

Then, edit the ``inbox`` namespace and add the following line::

  inbox = yes

In order for dovecot to automaticaly create usual folders on account creation, edit the ``inbox`` namespace of :file:`15-mailboxes.conf`::

  mailbox Drafts {
    auto = subscribe
    special_use = \Drafts
  }
  mailbox Junk {
    auto = subscribe
    special_use = \Junk
  }
  mailbox Sent {
    auto = subscribe
    special_use = \Sent
  }
  mailbox Trash {
    auto = subscribe
    special_use = \Trash
  }

Starting dovecot 2.2.20+, you can add ``autoexpunge`` parameter to delete older message, for instance::

  mailbox Trash {
    auto = subscribe
    special_use = \Trash
    autoexpunge=30d
  }

With dovecot 2.1+, it ensures all the special mailboxes will be
automaticaly created for new accounts.

For dovecot 2.0 and older, use the `autocreate
<http://wiki2.dovecot.org/Plugins/Autocreate>`_ plugin.

.. _fs_operations:

Operations on the file system
-----------------------------

.. warning::

   Modoboa needs to access the ``dovecot`` binary to check its
   version. To find the binary path, we use the ``which`` command
   first and then try known locations (:file:`/usr/sbin/dovecot` and
   :file:`/usr/local/sbin/dovecot`). If you installed dovecot in a
   custom location, please tell us where the binary is by using the
   ``DOVECOT_LOOKUP_PATH`` setting (see :file:`settings.py`).

Three operation types are considered:

#. Mailbox creation
#. Mailbox renaming
#. Mailbox deletion

The first one is managed by Dovecot. The last two ones may be managed
by Modoboa if it can access the file system where the mailboxes are
stored (see :ref:`admin-params` to activate this feature).

Those operations are treated asynchronously by a cron script. For
example, when you rename an e-mail address through the web UI, the
associated mailbox on the file system is not modified
directly. Instead of that, a *rename* order is created for this
mailbox. The mailbox will be considered unavailable until the order is
executed (see :ref:`Postfix configuration <postfix_config>`).

Edit the crontab of the user who owns the mailboxes on the file system::

  $ crontab -u <vmail_user> -e

And add the following line inside::

  * * * * * python <modoboa_instance>/manage.py handle_mailbox_operations

.. warning::

   The cron script must be executed by the system user owning the mailboxes.

.. warning::

   The user running the cron script must have access to the
   :file:`settings.py` file of the modoboa instance.

The result of each order is recorded into Modoboa's log. Go to
*Modoboa > Logs* to consult them.

.. _dovecot_authentication:

Authentication
==============

To make the authentication work, edit the :file:`conf.d/10-auth.conf` and
uncomment the following line at the end::

  #!include auth-system.conf.ext
  !include auth-sql.conf.ext
  #!include auth-ldap.conf.ext
  #!include auth-passwdfile.conf.ext
  #!include auth-checkpassword.conf.ext
  #!include auth-vpopmail.conf.ext
  #!include auth-static.conf.ext


Then, edit the :file:`conf.d/auth-sql.conf.ext` file and add the following
content inside::

  passdb sql {
    driver = sql
    # Path for SQL configuration file, see example-config/dovecot-sql.conf.ext
    args = /etc/dovecot/dovecot-sql.conf.ext
  }

  userdb sql {
    driver = sql
    args = /etc/dovecot/dovecot-sql.conf.ext
  }

Make sure to activate only one backend (per type) inside your configuration
(just comment the other ones).

Edit the :file:`dovecot-sql.conf.ext` and modify the configuration according
to your database engine.

.. _dovecot_mysql_queries:

MySQL users
-----------

For debian and derivative, you need to install mysql connector for dovecot::
  sudo apt install dovecot-mysql

::

  driver = mysql

  connect = host=<mysqld socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  user_query = \
    SELECT '%{home_dir}/%%d/%%n' AS home, %mailboxes_owner_uid as uid, \
    %mailboxes_owner_gid as gid, \
    CONCAT('*:bytes=', mb.quota, 'M') AS quota_rule \
    FROM admin_mailbox mb \
    INNER JOIN admin_domain dom ON mb.domain_id=dom.id \
    INNER JOIN core_user u ON u.id=mb.user_id \
    WHERE (mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) \
    AND mb.address='%%n' AND dom.name='%%d'

  password_query = \
    SELECT email AS user, password, '%{home_dir}/%%d/%%n' AS userdb_home, \
    %mailboxes_owner_uid AS userdb_uid, %mailboxes_owner_gid AS userdb_gid, \
    CONCAT('*:bytes=', mb.quota, 'M') AS userdb_quota_rule \
    FROM core_user u \
    INNER JOIN admin_mailbox mb ON u.id=mb.user_id \
    INNER JOIN admin_domain dom ON mb.domain_id=dom.id \
    WHERE (mb.is_send_only=0 OR '%s' NOT IN ('imap', 'pop3')) \
    AND u.email='%%u' AND u.is_active=1 AND dom.enabled=1

  iterate_query = SELECT email AS user FROM core_user WHERE is_active

.. _dovecot_pg_queries:

PostgreSQL users
----------------

For debian and derivative, you need to install postgres connector for dovecot::
  sudo apt install dovecot-pgsql

::

  driver = pgsql

  connect = host=<postgres socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  user_query = \
    SELECT '%{home_dir}/%%d/%%n' AS home, %mailboxes_owner_uid as uid, \
    %mailboxes_owner_gid as gid, '*:bytes=' || mb.quota || 'M' AS quota_rule \
    FROM admin_mailbox mb \
    INNER JOIN admin_domain dom ON mb.domain_id=dom.id \
    INNER JOIN core_user u ON u.id=mb.user_id \
    WHERE (mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3', 'lmtp')) \
    AND mb.address='%%n' AND dom.name='%%d'

  password_query = \
    SELECT email AS user, password, '%{home_dir}/%%d/%%n' AS userdb_home, \
    %mailboxes_owner_uid AS userdb_uid, %mailboxes_owner_gid AS userdb_gid, \
    CONCAT('*:bytes=', mb.quota, 'M') AS userdb_quota_rule \
    FROM core_user u \
    INNER JOIN admin_mailbox mb ON u.id=mb.user_id \
    INNER JOIN admin_domain dom ON mb.domain_id=dom.id \
    WHERE (mb.is_send_only IS NOT TRUE OR '%s' NOT IN ('imap', 'pop3'))\
    AND email='%%u' AND is_active AND dom.enabled

  iterate_query = SELECT email AS user FROM core_user WHERE is_active

SQLite users
------------

For debian and derivative, you need to install sqlite connector for dovecot::
  sudo apt install dovecot-sqlite

::

  driver = sqlite

  connect = <path to the sqlite db file>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE u.email='%Lu' AND u.is_active=1 AND dom.enabled=1

  user_query = SELECT '<mailboxes storage directory>/%Ld/%Ln' AS home, <uid> as uid, <gid> as gid, ('*:bytes=' || mb.quota || 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%Ln' AND dom.name='%Ld'

  iterate_query = SELECT email AS user FROM core_user

.. note::

   Replace values between ``<>`` with yours.

.. _dovecot_oauth2:

OAuth 2 authentication
======================

You first need to register Dovecot as an authorized consumer of the
OAuth2 authentication service provided by Modoboa. To do so, create an
application with the following commands:

.. sourcecode:: bash

   > cd <modoboa_instance_path>
   > python manage.py createapplication --name=Dovecot --skip-authorization --client-id=dovecot confidential client-credentials

On success, you should see an output similar to::

  New application Dovecot created successfully.
  client_secret: XXXX

To enable OAuth2 authentication in Dovecot, edit the :file:`conf.d/10-auth.conf`
file and update the auth_mechanisms line as follows::

  auth_mechanisms = plain login oauthbearer xoauth2

Then, add the following line at the end::

  !include auth-oauth2.conf.ext

Then, create a file named :file:`conf.d/auth-oauth2.conf.ext` with the
following content::

  passdb {
    driver = oauth2
    mechanisms = xoauth2 oauthbearer
    args = /etc/dovecot/conf.d/dovecot-oauth2.conf.ext
  }

Finally, create a file named :file:`conf.d/dovecot-oauth2.conf.ext` with the
following content::

  introspection_mode = post
  introspection_url = https://dovecot:<client_secret>@<hostname of your server>/api/o/introspect/
  username_attribute = username
  tls_ca_cert_file = /etc/ssl/certs/ca-certificates.crt
  active_attribute = active
  active_value = true

Replace ``<client_secret>`` with the value you obtained earlier.

LDAP
====
To make the LDAP authentication work, edit the :file:`conf.d/10-auth.conf` and
uncomment the following line at the end::

   !include auth-ldap.conf.ext

Then edit the :file:`conf.d/auth-ldap.conf.ext` and edit the passdb section as following.
You should comment the userdb section, which will be managed by SQL with modoboa database.::

   passdb {
      driver = ldap

      # Path for LDAP configuration file, see example-config/dovecot-ldap.conf.ext
      args = /etc/dovecot/dovecot-ldap.conf.ext
   }

   #userdb {
      #driver = ldap
      #args = /etc/dovecot/dovecot-ldap.conf.ext

      # Default fields can be used to specify defaults that LDAP may override
      #default_fields = home=/home/virtual/%u
   #}

Your own dovecot LDAP configuration file is now :file:`/etc/dovecot/dovecot-ldap.conf.ext`.
You can add your default LDAP conf in it, following the `official documentation <https://doc.dovecot.org/configuration_manual/authentication/ldap/>`_.

Synchronize dovecot LDAP conf with modoboa LDAP conf
----------------------------------------------------

To make dovecot LDAP configuration synchronized with modoboa LDAP configuration, you should create a dedicated dovecot conf file.
At the end of your dovecot configuration file (:file:`dovecot-ldap.conf.ext`), add the following line::

   !include_try dovecot-modoboa.conf.ext

Then, set modoboa parameter *Enable Dovecot LDAP sync* to *Yes*.
Then set the *Dovecot LDAP config file* following the previous step (*/etc/dovecot/dovecot-modoboa.conf.ext* in the example)

The last step is to add the command **update_dovecot_conf** to the cron job of modoboa.
Then, each time your modoboa LDAP configuration is updated, your dovecot LDAP configuration will also be.

LMTP
====

`Local Mail Transport Protocol
<http://en.wikipedia.org/wiki/Local_Mail_Transfer_Protocol>`_ is used
to let Postfix deliver messages to Dovecot.

First, make sure the protocol is activated by looking at the
``protocols`` setting (generally inside
:file:`dovecot.conf`). It should be similar to the following example::

  protocols = imap pop3 lmtp

Then, open the :file:`conf.d/10-master.conf`, look for ``lmtp``
service definition and add the following content inside::

  service lmtp {
    # stuff before
    unix_listener /var/spool/postfix/private/dovecot-lmtp {
      mode = 0600
      user = postfix
      group = postfix
    }
    # stuff after
  }

We assume here that Postfix is *chrooted* within
:file:`/var/spool/postfix`.

Finally, open the :file:`conf.d/20-lmtp.conf` and modify it as follows::

  protocol lmtp {
    postmaster_address = postmaster@<domain>
    mail_plugins = $mail_plugins quota sieve
  }

Replace ``<domain>`` by the appropriate value.

.. note::

   If you don't plan to apply quota or to use filters, just adapt the
   content of the ``mail_plugins`` setting.

.. _dovecot_quota:

Quota
=====

Modoboa lets adminstrators define per-domain and/or per-account limits
(quota). It also lists the current quota usage of each account. Those
features require Dovecot to be configured in a specific way.

Inside :file:`conf.d/10-mail.conf`, add the ``quota`` plugin to the default
activated ones::

  mail_plugins = quota

Inside :file:`conf.d/10-master.conf`, update the ``dict`` service to set
proper permissions::

  service dict {
    # If dict proxy is used, mail processes should have access to its socket.
    # For example: mode=0660, group=vmail and global mail_access_groups=vmail
    unix_listener dict {
      mode = 0600
      user = <user owning mailboxes>
      #group =
    }
  }

Inside :file:`conf.d/20-imap.conf`, activate the ``imap_quota`` plugin::

  protocol imap {
    # ...

    mail_plugins = $mail_plugins imap_quota

    # ...
  }

Inside :file:`dovecot.conf`, activate the quota SQL dictionary backend::

  dict {
    quota = <driver>:/etc/dovecot/dovecot-dict-sql.conf.ext
  }

Inside :file:`conf.d/90-quota.conf`, activate the *quota dictionary* backend::

  plugin {
    quota = dict:User quota::proxy::quota
  }

It will tell Dovecot to keep quota usage in the SQL dictionary.

Finally, edit the :file:`dovecot-dict-sql.conf.ext` file and put the
following content inside::

  connect = host=<db host> dbname=<db name> user=<db user> password=<password>
  # SQLite users
  # connect = /path/to/the/database.db

  map {
    pattern = priv/quota/storage
    table = admin_quota
    username_field = username
    value_field = bytes
  }
  map {
    pattern = priv/quota/messages
    table = admin_quota
    username_field = username
    value_field = messages
  }

*PostgreSQL* users
------------------

Database schema update
^^^^^^^^^^^^^^^^^^^^^^

The ``admin_quota`` table is created by Django but unfortunately it
doesn't support ``DEFAULT`` constraints (it only simulates them when the
ORM is used). As PostgreSQL is a bit strict about constraint
violations, you must execute the following query manually::

  db=> ALTER TABLE admin_quota ALTER COLUMN bytes SET DEFAULT 0;
  db=> ALTER TABLE admin_quota ALTER COLUMN messages SET DEFAULT 0;

Trigger
^^^^^^^

As indicated on `Dovecot's wiki
<http://wiki2.dovecot.org/Quota/Dict>`_, you need a trigger to
properly update the quota.

A working copy of this trigger is available on `Github <https://raw.githubusercontent.com/modoboa/modoboa-installer/master/modoboa_installer/scripts/files/dovecot/install_modoboa_postgres_trigger.sql>`_.

Download this file and copy it on the server running postgres. Then,
execute the following commands::

  $ su - postgres
  $ psql [modoboa database] < /path/to/modoboa_postgres_trigger.sql
  $ exit

Replace ``[modoboa database]`` by the appropriate value.

Forcing recalculation
---------------------

For existing installations, *Dovecot* (> 2) offers a command to
recalculate the current quota usages. For example, if you want to
update all usages, run the following command::

  $ doveadm quota recalc -A

Be carefull, it can take a while to execute.

ManageSieve/Sieve
=================

Modoboa lets users define filtering rules from the web interface. To
do so, it requires *ManageSieve* to be activated on your server.

Inside :file:`conf.d/20-managesieve.conf`, make sure the following lines are
uncommented::

  protocols = $protocols sieve

  service managesieve-login {
    # ...
  }

  service managesieve {
    # ...
  }

  protocol sieve {
    # ...
  }

Finally, configure the ``sieve`` plugin by editing the
:file:`conf.d/90-sieve.conf` file. Put the follwing caontent inside::

  plugin {
    # Location of the active script. When ManageSieve is used this is actually
    # a symlink pointing to the active script in the sieve storage directory.
    sieve = ~/.dovecot.sieve

    #
    # The path to the directory where the personal Sieve scripts are stored. For
    # ManageSieve this is where the uploaded scripts are stored.
    sieve_dir = ~/sieve
  }

Restart Dovecot.

Now, you can go to the :ref:`postfix` section to finish the installation.

.. _lastlogin:

Last-login tracking
===================

To update the ``last_login`` attribute of an account after a succesful
IMAP or POP3 login, you can configure a `post-login script
<https://wiki.dovecot.org/PostLoginScripting>`_.

Open :file:`conf.d/10-master.conf` add the following configuration
(``imap`` and ``pop3`` services are already defined, you just need to
update them)::

  service imap {
    executable = imap postlogin
  }

  service pop3 {
    executable = pop3 postlogin
  }

  service postlogin {
    executable = script-login /usr/local/bin/postlogin.sh
    user = modoboa
    unix_listener postlogin {
    }
  }

Then, you must create a script named
:file:`/usr/local/bin/postlogin.sh`. According to your database
engine, the content will differ.

PostgreSQL
----------

.. sourcecode:: bash

   #!/bin/sh

   psql -c "UPDATE core_user SET last_login=now() WHERE username='$USER'" > /dev/null

   exec "$@"

MySQL
-----

.. sourcecode:: bash

   #!/bin/sh

   DBNAME=XXX
   DBUSER=XXX
   DBPASSWORD=XXX

   echo "UPDATE core_user SET last_login=now() WHERE username='$USER'" | mysql -u $DBUSER -p$DBPASSWORD $DBNAME

   exec "$@"
