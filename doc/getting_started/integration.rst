#################################
Integration with other components
#################################

***********************
External authentication
***********************

LDAP
====

*Modoboa* supports external LDAP authentication using the following extra components:

* `Python LDAP client <http://www.python-ldap.org/>`_
* `Django LDAP authentication backend <http://pypi.python.org/pypi/django-auth-ldap>`_

If you want to use this feature, you must first install those components::

  $ easy_install python-ldap django-auth-ldap

Then, all you have to do is to modify the `settings.py` file:

* Add a new authentication backend to the `AUTHENTICATION_BACKENDS`
  variable, like this::

    AUTHENTICATION_BACKENDS = (
      'django_auth_ldap.backend.LDAPBackend',
      'modoboa.lib.authbackends.SimpleBackend',
      'django.contrib.auth.backends.ModelBackend',
    )

* Set the required parameters to establish the communication with your
  LDAP server, for example::

    import ldap
    from django_auth_ldap.config import LDAPSearch

    AUTH_LDAP_BIND_DN = ""
    AUTH_LDAP_BIND_PASSWORD = ""
    LDAP_USER_BASE = "ou=users,dc=example,dc=com"	
    LDAP_USER_FILTER = "(mail=%(user)s)"
    AUTH_LDAP_USER_SEARCH = LDAPSearch(LDAP_USER_BASE,
        ldap.SCOPE_SUBTREE, LDAP_USER_FILTER)

You will find a detailled documentation `here
<http://packages.python.org/django-auth-ldap/>`_.

Once the authentication is properly configured, the users defined in
your LDAP directory will be able to connect to *Modoboa*, the associated
domain and mailboxes will be automatically created if needed.

Users will also be able to update their LDAP password directly from
Modoboa.

.. note:: 

   Modoboa doesn't provide any synchronization mechanism once a user
   is registered into the database. Any modification done from the
   directory to a user account will not be reported to Modoboa (an
   email address change for example). Currently, the only solution is
   to manually delete the Modoboa record, it will be recreated on the
   next user login.

Available settings
------------------

* ``LDAP_USER_BASE`` : the distinguish name of the search base
* ``LDAP_USER_FILTER`` : the filter used to retrieve users distinguish name
* ``LDAP_PASSWORD_ATTR`` : the attribute used to store the password
  (default: ``userPassword``)
* ``LDAP_ACTIVE_DIRECTORY`` : used to indicate if your directory is an
  Active Directory one (default: ``False``)

.. _postfix:

*******
Postfix
*******

For *MySQL* users, define the following map files on your server (it should work with
*postfix* versions >= 2.2):

``/etc/postfix/sql-domains.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT name FROM admin_domain WHERE name='%s' AND enabled=1

``/etc/postfix/sql-domain-aliases.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT dom.name FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id WHERE domal.name='%s' AND domal.enabled=1 AND dom.enabled=1

``/etc/postfix/sql-mailboxes.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT concat(dom.name, '/', mb.path, (SELECT value FROM lib_parameter WHERE name='admin.MAILDIR_ROOT'), '/') FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN auth_user user ON mb.user_id=user.id WHERE dom.enabled=1 AND dom.name='%d' AND user.is_active=1 AND mb.address='%u'

``/etc/postfix/sql-aliases.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = (SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias_mboxes al_mb INNER JOIN admin_alias al ON al_mb.alias_id=al.id INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE dom.name='%d' AND dom.enabled=1 AND al.address='%u' AND al.enabled=1 AND al.extmboxes<>'')

``/etc/postfix/sql-domain-aliases-mailboxes.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT concat(mb.address, '@', dom.name) FROM admin_domain dom INNER JOIN admin_domainalias domal ON dom.id=domal.target_id INNER JOIN admin_mailbox mb ON dom.id=mb.domain_id WHERE domal.name='%d' AND domal.enabled=1 AND mb.address='%u' 

Then, use the following configuration in the */etc/postfix/main.cf* file
(this is just one possible configuration)::

  # Stuff before
  mailbox_transport = virtual
  maildrop_destination_recipient_limit = 1
  virtual_minimum_uid = <vmail user id> 
  virtual_gid_maps = static:<vmail group id>
  virtual_uid_maps = static:<vmail user id>
  virtual_mailbox_base = /var/vmail

  relay_domains = 
  virtual_mailbox_domains = mysql:/etc/postfix/sql-domains.cf
  virtual_alias_domains = mysql:/etc/postfix/sql-domain-aliases.cf
  virtual_mailbox_maps = mysql:/etc/postfix/sql-mailboxes.cf
  virtual_alias_maps = mysql:/etc/postfix/sql-aliases.cf,
        mysql:/etc/postfix/sql-domain-aliases-mailboxes.cf
  # Stuff after

.. note::
   Modoboa supports both maildir and mbox formats. You can specify
   which format to use by modifying the MAILBOX_TYPE parameter available
   in the admin panel.

Optional : 'catchall' aliases
=============================

Modoboa supports 'catchall' aliases creation. In the case you would
like to use this feature, you'll need to add specific queries to
*postfix* configuration.

First, create the following new maps (*MySQL* users):

``/etc/postfix/sql-email2email.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1e
  query = SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN auth_user user ON mb.user_id=user.id WHERE dom.name='%d' AND dom.enabled=1 AND mb.address='%u' AND user.is_active=1

``/etc/postfix/sql-catchall-aliases.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = (SELECT concat(mb.address, '@', dom.name) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.id IN (SELECT al_mb.mailbox_id FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id INNER JOIN admin_alias_mboxes al_mb ON al.id=al_mb.alias_id WHERE al.enabled=1 AND al.address='*' AND dom.name='%d' AND dom.enabled=1)) UNION (SELECT al.extmboxes FROM admin_alias al INNER JOIN admin_domain dom ON al.domain_id=dom.id WHERE al.enabled='1' AND al.extmboxes<>'' AND al.address='*' AND dom.name='%d' AND dom.enabled=1)

Once done, edit the *main.cf* configuration file and add the new maps
to the ``virtual_alias_maps`` parameter like this::

   virtual_alias_maps = mysql:/etc/postfix/sql-aliases.cf,
        mysql:/etc/postfix/sql-domain-aliases-mailboxes.cf,
        mysql:/etc/postfix/sql-email2email.cf,                  # new
        mysql:/etc/postfix/sql-catchall-aliases.cf              # new

Reload *postfix*.

.. _dovecot_lda:

Optional: using Dovecot's LDA
=============================

If you are using *Dovecot* in your environnement, I recommend to use
its LDA. Doing so, you'll will be able to use extra functionalities
such as sieve filters and more.

First, edit the */etc/postfix/main.cf* file and define (or modify if
they already exist) the following parameters::

  virtual_transport = dovecot
  dovecot_destination_recipient_limit = 1

Then, edit the */etc/postfix/master.cf* file and add the following
definition at the end::

  dovecot   unix  -       n       n       -       -       pipe
    flags=DRhu user=vmail:vmail argv=/usr/lib/dovecot/deliver -f ${sender} -d ${recipient}

If you have followed the :ref:`postfix` section to install your
environnement, you need to modify the SQL query corresponding to the
``virtual_mailbox_maps`` parameter. Edit the
*/etc/postfix/maps/sql-mailboxes.cf* and modify the ``query``
parameter as follow::

  query = SELECT concat(dom.name, '/', mb.path) FROM admin_mailbox mb INNER JOIN admin_domain dom ON mb.domain_id=dom.id INNER JOIN auth_user user ON mb.user_id=user.id WHERE dom.enabled=1 AND dom.name='%d' AND user.is_active=1 AND mb.address='%u'

Restart *Postfix*.

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
  password_query = SELECT email AS user, password FROM auth_user WHERE email='%u' and is_active=1
  user_query = SELECT concat(dom.name, '/', mb.path) AS home, uid, gid FROM admin_mailbox mb INNER JOIN auth_user user ON mb.user_id=user.id INNER JOIN admin_domain dom ON mb.domain_id=dom.id WHERE mb.address='%n' AND dom.name='%d' AND user.is_active=1 AND dom.enabled=1

Enable quotas support
=====================

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

   If you're using *Postfix* as MTA, you will have to use *Dovecot*'s
   local delivery agent otherwise your emails won't get filtered. See
   :ref:`dovecot_lda` to get information on how to activate this.
