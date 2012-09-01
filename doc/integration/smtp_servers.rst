############
SMTP servers
############

.. _postfix:

*******
Postfix
*******

This section gives an example about building a simple virtual hosting
configuration with *Postfix*. Refer to the `official documentation
<http://www.postfix.org/VIRTUAL_README.html>`_ for more explanation.

.. note::

   The SQL queries presented below are working well with MySQL
   only. To make them work with PostgreSQL, just replace (when needed)
   the `concat` function call by the standard concatenation operator
   (ie. `||`).

Define the following map files on your server (it should work with
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
  query = SELECT DISTINCT concat(mb.address, '@', dom.name) FROM admin_alias al INNER JOIN admin_domain dom ON dom.id=al.domain_id INNER JOIN admin_domainalias domal ON domal.target_id=dom.id INNER JOIN (admin_alias_mboxes almb, admin_mailbox mb) ON (almb.alias_id=al.id AND almb.mailbox_id=mb.id) WHERE domal.name='%d' AND domal.enabled=1 AND (al.address='%u' OR mb.address='%u')

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
