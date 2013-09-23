###################
Dovecot and Postfix
###################

.. _dovecot:

*******
Dovecot
*******

Modoboa works better with Dovecot 2.0 so the following documentation
is suitable for this combination.

In this section, we assume dovecot's configuration resides in
:file:`/etc/dovecot`, all pathes will be relative to this directory.

Mailboxes
=========

First, edit the :file:`conf.d/10-mail.conf` and set the ``mail_location``
variable::

  # maildir
  mail_location = maildir:~/.maildir

Then, edit the ``inbox`` namespace and add the following lines::

  mailbox Drafts {
    auto = create
    special_use = \Drafts
  }
  mailbox Junk {
    auto = create
    special_use = \Junk
  }
  mailbox Sent {
    auto = create
    special_use = \Sent
  }
  mailbox Trash {
    auto = create
    special_use = \Trash
  }

It ensures all the special mailboxes will be automaticaly created for
new accounts.

.. _fs_operations:

Operations on the file system
-----------------------------

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
not executed (see :ref:`Postfix configuration <postfix_config>`).

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

  password_query = SELECT email AS user, password FROM admin_user WHERE email='%u' and is_active=1

  user_query = SELECT '<mailboxes storage directory>/%d/%n' AS home, <uid> as uid, <gid> as gid, concat('*:bytes=', mb.quota, 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d'

  iterate_query = SELECT email AS username FROM admin_user

.. _dovecot_pg_queries:

PostgreSQL users
----------------

::

  driver = postgresql

  connect = host=<postgres socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM admin_user WHERE email='%u' and is_active

  user_query = SELECT '<mailboxes storage directory>/%d/%n' AS home, <uid> as uid, <gid> as gid, '*:bytes=' || mb.quota || 'M' AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d'

  iterate_query = SELECT email AS username FROM admin_user

.. note::

   Replace values between ``<>`` with yours.

LDA
===

The LDA is activated by default but you must define a *postmaster*
address. Open the :file:`conf.d/15-lda.conf` file modify the following line::

  postmaster_address = postmaster@<domain>

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
properly update the quota. Unfortunately, the provided example won't
work for Modoboa. You should use the following one instead:

.. sourcecode:: sql

  CREATE OR REPLACE FUNCTION merge_quota() RETURNS TRIGGER AS $$
  BEGIN
    IF NEW.messages < 0 OR NEW.messages IS NULL THEN
      -- ugly kludge: we came here from this function, really do try to insert
      IF NEW.messages IS NULL THEN
        NEW.messages = 0;
      ELSE
        NEW.messages = -NEW.messages;
      END IF;
      return NEW;
    END IF;

    LOOP
      UPDATE admin_quota SET bytes = bytes + NEW.bytes,
        messages = messages + NEW.messages
        WHERE username = NEW.username;
      IF found THEN
        RETURN NULL;
      END IF;

      BEGIN
        IF NEW.messages = 0 THEN
          RETURN NEW;
        ELSE
          NEW.messages = - NEW.messages;
          return NEW;
        END IF;
      EXCEPTION WHEN unique_violation THEN
        -- someone just inserted the record, update it
      END;
    END LOOP;
  END;
  $$ LANGUAGE plpgsql;

  CREATE OR REPLACE FUNCTION set_mboxid() RETURNS TRIGGER AS $$
  DECLARE
    mboxid INTEGER;
  BEGIN
    SELECT admin_mailbox.id INTO STRICT mboxid FROM admin_mailbox INNER JOIN admin_user ON admin_mailbox.user_id=admin_user.id WHERE admin_user.username=NEW.username;
    UPDATE admin_quota SET mbox_id = mboxid
      WHERE username = NEW.username;
    RETURN NULL;
  END;
  $$ LANGUAGE plpgsql;

  DROP TRIGGER IF EXISTS mergequota ON admin_quota;
  CREATE TRIGGER mergequota BEFORE INSERT ON admin_quota
     FOR EACH ROW EXECUTE PROCEDURE merge_quota();

  DROP TRIGGER IF EXISTS setmboxid ON admin_quota;
  CREATE TRIGGER setmboxid AFTER INSERT ON admin_quota
     FOR EACH ROW EXECUTE PROCEDURE set_mboxid();

Copy this example into a file (for example: :file:`quota-trigger.sql`) on
server running postgres and execute the following commands::

  $ su - postgres
  $ psql < /path/to/quota-trigger.sql
  $ exit

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

.. _postfix:

*******
Postfix
*******

This section gives an example about building a simple virtual hosting
configuration with *Postfix*. Refer to the `official documentation
<http://www.postfix.org/VIRTUAL_README.html>`_ for more explanation.

Map files
=========

You first need to create configuration files (or map files) that will
be used by Postfix to lookup into Modoboa tables.

To automaticaly generate the requested map files and store them in a
directory, run the following command::

  $ modoboa-admin.py postfix_maps --dbtype <mysql|postgres> mapfiles

:file:`mapfiles` is the directory where the files will be
stored. Answer the few questions and you're done.

.. _postfix_config:

Configuration
=============

Use the following configuration in the :file:`/etc/postfix/main.cf` file
(this is just one possible configuration)::

  # Stuff before
  virtual_transport = dovecot
  dovecot_destination_recipient_limit = 1

  virtual_minimum_uid = <vmail user id> 
  virtual_gid_maps = static:<vmail group id>
  virtual_uid_maps = static:<vmail user id>
  virtual_mailbox_base = /var/vmail

  relay_domains = 
  virtual_mailbox_domains = mysql:/etc/postfix/sql-domains.cf
  virtual_alias_domains = mysql:/etc/postfix/sql-domain-aliases.cf
  virtual_mailbox_maps = mysql:/etc/postfix/sql-mailboxes.cf
  virtual_alias_maps = mysql:/etc/postfix/sql-aliases.cf,
        mysql:/etc/postfix/sql-domain-aliases-mailboxes.cf,
        mysql:/etc/postfix/sql-email2email.cf,
        mysql:/etc/postfix/sql-catchall-aliases.cf

  smtpd_recipient_restrictions =
        ...
        check_recipient_access mysql:/etc/postfix/maps/sql-maintain.cf
        permit_mynetworks
        ...

  # Stuff after

Then, edit the :file:`/etc/postfix/master.cf` file and add the following
definition at the end::

  dovecot   unix  -       n       n       -       -       pipe
    flags=DRhu user=vmail:vmail argv=/usr/lib/dovecot/deliver -f ${sender} -d ${recipient}

Restart Postfix.
