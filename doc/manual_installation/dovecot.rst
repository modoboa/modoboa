.. _dovecot:

#######
Dovecot
#######

Modoboa requires Dovecot 2+ to work so the following documentation is
suitable for this combination.

In this section, we assume dovecot's configuration resides in
:file:`/etc/dovecot`, all pathes will be relative to this directory.

Mailboxes
=========

First, edit the :file:`conf.d/10-mail.conf` and set the ``mail_location``
variable::

  # maildir
  mail_location = maildir:~/.maildir

Then, edit the ``inbox`` namespace and add the following lines::

  inbox = yes

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

  $ crontab -u <user> -e

And add the following line inside::

  * * * * * python <modoboa_site>/manage.py handle_mailbox_operations

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

::

  driver = mysql

  connect = host=<mysqld socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM core_user WHERE email='%Lu' and is_active=1

   user_query = SELECT '<mailboxes storage directory>/%Ld/%Ln' AS home, <uid> as uid, <gid> as gid, concat('*:bytes=', mb.quota, 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%Ln' AND dom.name='%Ld'

  iterate_query = SELECT email AS user FROM core_user

.. _dovecot_pg_queries:

PostgreSQL users
----------------

::

  driver = pgsql

  connect = host=<postgres socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE u.email='%Lu' AND u.is_active AND dom.enabled

  user_query = SELECT '<mailboxes storage directory>/%Ld/%Ln' AS home, <uid> as uid, <gid> as gid, '*:bytes=' || mb.quota || 'M' AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%Ln' AND dom.name='%Ld'

  iterate_query = SELECT email AS user FROM core_user

SQLite users
------------

::

  driver = sqlite

  connect = <path to the sqlite db file>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM core_user u INNER JOIN admin_mailbox mb ON u.id=mb.user_id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE u.email='%Lu' AND u.is_active=1 AND dom.enabled=1

  user_query = SELECT '<mailboxes storage directory>/%Ld/%Ln' AS home, <uid> as uid, <gid> as gid, ('*:bytes=' || mb.quota || 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%Ln' AND dom.name='%Ld'

  iterate_query = SELECT email AS user FROM core_user

.. note::

   Replace values between ``<>`` with yours.

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

Messages filtering using Sieve is done by the LDA.

Inside :file:`conf.d/15-lda.conf`, activate the ``sieve`` plugin like this::

  protocol lda {
    # Space separated list of plugins to load (default is global mail_plugins).
    mail_plugins = $mail_plugins sieve
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
