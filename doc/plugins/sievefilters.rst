#############
Sieve filters
#############

This plugin let users create server-side message filters, using the
`sievelib module <http://pypi.python.org/pypi/sievelib>`_ (which
provides Sieve and ManageSieve clients).

Two working modes are available:

* A raw mode: you create filters using the Sieve language directly
  (advanced users)
* An assisted mode: you create filters using an intuitive form

To use this plugin, your hosting setup must include a *ManageSieve*
server and your local delivery agent must understand the *Sieve*
language. Don't panic, Dovecot supports both :-) (refer to
:ref:`dovecot` to know how to enable those features).

.. note:: 
   The sieve filters plugin requires that the :ref:`webmail` plugin is
   activated and configured.

Go the online panel and modify the following parameters in order to
communicate with the *ManageSieve* server:

+--------------------+--------------------+--------------------+
|Name                |Description         |Default value       |
+====================+====================+====================+
|Server address      |Address of your     |127.0.0.1           |
|                    |MANAGESIEVE server  |                    |
+--------------------+--------------------+--------------------+
|Server port         |Listening port of   |4190                |
|                    |your MANAGESIEVE    |                    |
|                    |server              |                    |
+--------------------+--------------------+--------------------+
|Connect using       |Use the STARTTLS    |no                  |
|STARTTLS            |extension           |                    |
+--------------------+--------------------+--------------------+
|Authentication      |Prefered            |auto                |
|mechanism           |authentication      |                    |
|                    |mechanism           |                    |
+--------------------+--------------------+--------------------+
