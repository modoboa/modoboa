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
*/etc/dovecot*, all pathes will be relative to this directory.

Mailboxes
=========

First, edit the *conf.d/10-mail.conf* and set the ``mail_location``
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

.. note::

   Modoboa is not responsible for mailboxes creation, Dovecot is.

Authentication
==============

To make the authentication work, edit the *conf.d/10-auth.conf* and
uncomment the following line at the end::

  #!include auth-system.conf.ext
  !include auth-sql.conf.ext
  #!include auth-ldap.conf.ext
  #!include auth-passwdfile.conf.ext
  #!include auth-checkpassword.conf.ext
  #!include auth-vpopmail.conf.ext
  #!include auth-static.conf.ext


Then, edit the *conf.d/auth-sql.conf.ext* file and add the following
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

*MySQL* users, edit the *dovecot-sql.conf.ext* file and modify following lines::

  driver = mysql

  connect = host=<mysqld socket> dbname=<database> user=<user> password=<password>

  default_pass_scheme = CRYPT

  password_query = SELECT email AS user, password FROM admin_user WHERE email='%u' and is_active=1

  user_query = SELECT '<mailboxes storage directory>/%d/%n' AS home, <uid> as uid, <gid> as gid, concat('*:bytes=', mb.quota, 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d'

  iterate_query = SELECT email AS username FROM admin_user

*PostgreSQL* users, here is your version::

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
address. Open the *conf.d/15-lda.conf* file modify the following line::

  postmaster_address = postmaster@<domain>

Quota
=====

Modoboa lets adminstrators define per-domain and/or per-account limits
(quota). It also lists the current quota usage of each account. Those
features require Dovecot to be configured in a specific way.

Inside *conf.d/10-mail.conf*, add the ``quota`` plugin to the default
activated ones::

  mail_plugins = quota

Inside *conf.d/20-imap.conf*, activate the ``imap_quota`` plugin::

  protocol imap {
    # ...

    mail_plugins = $mail_plugins imap_quota

    # ...
  }

Inside *dovecot.conf*, activate the quota SQL dictionary backend::

  dict {
    quota = <driver>:/etc/dovecot/dovecot-dict-sql.conf.ext
  }

Inside *conf.d/90-quota.conf*, activate the *quota dictionary* backend::

  plugin {
    quota = dict:User quota::proxy::quota
  }

It will tell Dovecot to keep quota usage in the SQL dictionary.

Finally, edit the *dovecot-dict-sql.conf* file and put the following content inside::

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


ManageSieve/Sieve
=================

Modoboa lets users define filtering rules from the web interface. To
do so, it requires *ManageSieve* to be activated on your server.

Inside *conf.d/20-managesieve.conf*, make sure the following lines are
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

Inside *conf.d/15-lda.conf*, activate the ``sieve`` plugin like this::

  protocol lda {
    # Space separated list of plugins to load (default is global mail_plugins).
    mail_plugins = $mail_plugins sieve
  }

Finally, configure the ``sieve`` plugin by editing the
*conf.d/90-sieve.conf* file. Put the follwing content inside::

  plugin {
    # Location of the active script. When ManageSieve is used this is actually 
    # a symlink pointing to the active script in the sieve storage directory.
    sieve = ~/.dovecot.sieve

    #
    # The path to the directory where the personal Sieve scripts are stored. For 
    # ManageSieve this is where the uploaded scripts are stored.
    sieve_dir = ~/sieve
  }

Restart *Dovecot*.

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
be used by *postfix* to lookup into Modoboa tables.

To automaticaly generate the requested map files and store them in a
directory, run the following command::

  $ modoboa-admin.py postfix_maps --dbtype <mysql|postgres> mapfiles

``mapfiles`` is the directory where the files will be stored. Answer the
few questions and you're done.

Configuration
=============

Use the following configuration in the */etc/postfix/main.cf* file
(this is just one possible configuration)::

  # Stuff before
  mailbox_transport = dovecot
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

  # Stuff after

Then, edit the */etc/postfix/master.cf* file and add the following
definition at the end::

  dovecot   unix  -       n       n       -       -       pipe
    flags=DRhu user=vmail:vmail argv=/usr/lib/dovecot/deliver -f ${sender} -d ${recipient}

Restart *Postfix*.
