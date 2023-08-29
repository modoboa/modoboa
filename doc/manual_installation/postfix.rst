.. _postfix:

#######
Postfix
#######

This section gives an example about building a simple virtual hosting
configuration with *Postfix*. Refer to the `official documentation
<http://www.postfix.org/VIRTUAL_README.html>`_ for more explanation.

Map files
=========

You first need to create configuration files (or map files) that will
be used by Postfix to lookup into Modoboa tables.

To automaticaly generate the requested map files and store them in a
directory, run the following command:

.. sourcecode:: bash

   > cd <modoboa_instance_path>
   > python manage.py generate_postfix_maps --destdir <directory>

``<directory>`` is the directory where the files will be
stored. Answer the few questions and you're done.

.. _postfix_config:

Configuration
=============

Use the following configuration in the :file:`/etc/postfix/main.cf` file. For TLS configuration, you can look at the
`used configuration <https://github.com/modoboa/modoboa-installer/blob/master/modoboa_installer/scripts/files/postfix/main.cf.tpl>`_
for `modoboa installer <https://github.com/modoboa/modoboa-installer>`_.
(this is just one possible configuration)::

  # Stuff before
  unknown_local_recipient_reject_code = 550
  unverified_recipient_reject_code = 550

  # appending .domain is the MUA's job.
  append_dot_mydomain = no

  ## Proxy maps
  proxy_read_maps =
        proxy:unix:passwd.byname
        proxy:<driver>:/etc/postfix/sql-domains.cf
        proxy:<driver>:/etc/postfix/sql-domain-aliases.cf
        proxy:<driver>:/etc/postfix/sql-aliases.cf
        proxy:<driver>:/etc/postfix/sql-relaydomains.cf
        proxy:<driver>:/etc/postfix/sql-maintain.cf
        proxy:<driver>:/etc/postfix/sql-relay-recipient-verification.cf
        proxy:<driver>:/etc/postfix/sql-sender-login-map.cf
        proxy:<driver>:/etc/postfix/sql-spliteddomains-transport.cf
        proxy:<driver>:/etc/postfix/sql-transport.cf

  ## Virtual transport settings
  virtual_transport = lmtp:unix:private/dovecot-lmtp

  virtual_mailbox_domains = proxy:<driver>:/etc/postfix/sql-domains.cf
  virtual_alias_domains = proxy:<driver>:/etc/postfix/sql-domain-aliases.cf
  virtual_alias_maps = proxy:<driver>:/etc/postfix/sql-aliases.cf

  ## Relay domains
  relay_domains = proxy:<driver>:/etc/postfix/sql-relaydomains.cf
  transport_maps =
    proxy:<driver>:/etc/postfix/sql-transport.cf
    proxy:<driver>:/etc/postfix/sql-spliteddomains-transport.cf

  smtpd_recipient_restrictions =
        permit_mynetworks
        permit_sasl_authenticated
        check_recipient_access
            proxy:<driver>:/etc/postfix/sql-maintain.cf
            proxy:<driver>:/etc/postfix/sql-relay-recipient-verification.cf
        reject_unverified_recipient
        reject_unauth_destination
        reject_non_fqdn_sender
        reject_non_fqdn_recipient
        reject_non_fqdn_helo_hostname

  smtpd_sender_login_maps = proxy:<driver>:/etc/postfix/sql-sender-login-map.cf

  # Stuff after

Replace ``<driver>`` by the name of the database you use.

Restart Postfix.

.. _policyd_config:

Policy daemon
-------------

If you want to enable the built-in policy daemon, add the following
content to the :file:`/etc/postfix/main.cf` file::

    smtpd_recipient_restrictions =
        # ...
        check_policy_service inet:localhost:9999
        # ...

And reload postfix.

.. note::

   The ``check_policy_service`` line must be placed before the
   ``permit_mynetworks`` one, otherwise the daemon won't be called.
