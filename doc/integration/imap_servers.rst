############
IMAP servers
############

.. _dovecot:

*******
Dovecot
*******

If you are using the *maildir* format to store mailboxes, add the
following line into Dovecot's main config file
(*/etc/dovecot/dovecot.conf*)::

  mail_location = maildir:<path_to_mailboxes>/%h/.maildir

The ``.maildir`` part is the previous example must match the value of
the ``MAILDIR_ROOT`` parameter. See :ref:`admin-params`.

If you are using the mbox format, add the following::
  
  mail_location = mbox:<path_to_mailboxes>/%h/:INBOX=<path_to_mailboxes>/%h/Inbox

To make the authentication work, edit *dovecot.conf* and add the
following content inside::

  auth default {
    # ... stuff before

    passdb sql {
      # Path for SQL configuration file, see /etc/dovecot/dovecot-sql.conf for
      #  example
      args = /etc/dovecot/dovecot-sql.conf
    }
    
    userdb sql {
      # Path for SQL configuration file
      args = /etc/dovecot/dovecot-sql.conf
    }

    # ... stuff after
  }

Make sure to activate only one backend (per type) inside your configuration
(just comment the other ones).

For *MySQL* users, edit your */etc/dovecot/dovecot-sql.conf* and modify following lines::

  driver = mysql
  connect = host=<mysqld socket> dbname=<database> user=<user> password=<password>
  default_pass_scheme = CRYPT
  password_query = SELECT email AS user, password FROM admin_user WHERE email='%u' and is_active=1
  user_query = SELECT concat(dom.name, '/', mb.path) AS home, uid, gid FROM admin_mailbox mb INNER JOIN admin_user user ON mb.user_id=user.id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d' AND user.is_active=1 AND dom.enabled=1

Enable quota support
====================

Put the following lines inside the *dovecot.conf* file::

    protocol imap {
      mail_plugins = quota imap_quota
    }

Before continuing, you need to know which quota backend must be used
(function of mailboxes format):

* mbox : backend=dirsize,
* maildir : backend=maildir.

If you use version prior to 1.1, add also the following configuration::

  plugin {
    # 10 MB default quota limit
    quota = <backend>:storage=10240
  }

For *MySQL* users, modify the above query inside *dovecot-sql.conf* as
follow to activate per-user quotas::

  user_query = SELECT concat(dom.name, '/', mb.path) AS home, uid, gid, concat('<backend>:storage=', mb.quota / 1024) AS quota FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d'

For version >= 1.1, put the following configuration inside the *dovecot.conf* file::

  plugin {
    # Default 10M storage limit with an extra 5M limit when saving to Trash.
    quota = <backend>:User quota
    quota_rule = *:storage=10M
    quota_rule2 = Trash:storage=5M
  }

For *MySQL* users, modify the above query inside *dovecot-sql.conf* to
activate per-user quotas::

  user_query = SELECT concat(dom.name, '/', mb.path) AS home, uid, gid, concat('*:storage=', mb.quota, 'M') AS quota_rule FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d'

Enable ManageSieve/Sieve support
================================

.. note:: 
   The following configuration example should work with versions
   1.X. For versions >= 2, please refer to `Dovecot's wiki
   <http://wiki2.dovecot.org/>`_.

Edit the */etc/dovecot/dovecot.conf* file and make the following
modifications:

* Add ``managesieve`` to the ``protocols`` variable::

    protocols = imap imaps managesieve

* Uncomment the ``managesieve`` section::

    protocol managesieve {
      # ...
    }

* Configure the ``lda`` protocol as follow::

    protocol lda {
      postmaster_address = postmaster@<your domain>
      mail_plugins = sieve # + your other plugins
      # ...
    }

* In the ``plugin`` section, uncomment the following content::

    plugin {
      # stuff before

      # Location of the active script. When ManageSieve is used this is actually 
      # a symlink pointing to the active script in the sieve storage directory.
      sieve=~/.dovecot.sieve

      #
      # The path to the directory where the personal Sieve scripts are stored. For 
      # ManageSieve this is where the uploaded scripts are stored.
      sieve_dir=~/sieve
    }

Restart *Dovecot*.

.. note::

   If you're using *Postfix* as MTA, you have to use *Dovecot*'s local
   delivery agent otherwise your emails won't get filtered. See
   :ref:`dovecot_lda` to get information on how to activate it.
