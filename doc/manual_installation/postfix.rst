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

Use the following configuration in the :file:`/etc/postfix/main.cf` file
(this is just one possible configuration)::

  # Stuff before
  virtual_transport = lmtp:unix:private/dovecot-lmtp

  virtual_mailbox_domains = <driver>:/etc/postfix/sql-domains.cf
  virtual_alias_domains = <driver>:/etc/postfix/sql-domain-aliases.cf
  virtual_alias_maps = <driver>:/etc/postfix/sql-aliases.cf

  relay_domains = <driver>:/etc/postfix/sql-relaydomains.cf
  transport_maps =
    <driver>:/etc/postfix/sql-transport.cf
    <driver>:/etc/postfix/sql-spliteddomains-transport.cf

  smtpd_recipient_restrictions =
        # ...
        check_recipient_access
            <driver>:/etc/postfix/sql-maintain.cf
            <driver>:/etc/postfix/sql-relay-recipient-verification.cf
        permit_mynetworks
        reject_unauth_destination
        reject_unverified_recipient
        # ...

  smtpd_sender_login_maps = <driver>:/etc/postfix/sql-sender-login-map.cf

  smtpd_sender_restrictions =
        reject_sender_login_mismatch

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
